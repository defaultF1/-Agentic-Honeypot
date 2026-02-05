import google.generativeai as genai
import json
import re
import time
import random
import asyncio
from typing import Dict, Any, Optional
from functools import wraps
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


@dataclass
class CircuitBreakerState:
    """Tracks circuit breaker state."""

    failures: int = 0
    last_failure: Optional[datetime] = None
    state: str = "closed"  # closed, open, half-open
    threshold: int = 5
    recovery_timeout: int = 30  # seconds


class CircuitBreaker:
    """Circuit breaker pattern for LLM calls."""

    def __init__(self, threshold: int = 5, recovery_timeout: int = 30):
        self.threshold = threshold
        self.recovery_timeout = recovery_timeout
        self.state = CircuitBreakerState(
            threshold=threshold, recovery_timeout=recovery_timeout
        )

    def can_execute(self) -> bool:
        """Check if we can execute the operation."""
        if self.state.state == "closed":
            return True

        if self.state.state == "open":
            # Check if recovery timeout has passed
            if self.state.last_failure:
                elapsed = (datetime.utcnow() - self.state.last_failure).total_seconds()
                if elapsed > self.recovery_timeout:
                    self.state.state = "half-open"
                    logger.info("Circuit breaker moved to half-open state")
                    return True
            return False

        if self.state.state == "half-open":
            return True

        return True

    def record_success(self):
        """Record a successful execution."""
        if self.state.state == "half-open":
            self.state.state = "closed"
            self.state.failures = 0
            logger.info("Circuit breaker closed after successful test")
        else:
            self.state.failures = max(0, self.state.failures - 1)

    def record_failure(self):
        """Record a failed execution."""
        self.state.failures += 1
        self.state.last_failure = datetime.utcnow()

        if self.state.failures >= self.state.threshold:
            if self.state.state != "open":
                self.state.state = "open"
                logger.warning(
                    f"Circuit breaker opened after {self.state.failures} failures"
                )


def retry_with_backoff(
    max_retries: int = 3, base_delay: float = 1.0, max_delay: float = 10.0
):
    """Decorator for retry logic with exponential backoff."""

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None

            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e

                    if attempt < max_retries:
                        # Calculate delay with jitter
                        delay = min(base_delay * (2**attempt), max_delay)
                        jitter = random.uniform(0, delay * 0.1)  # 10% jitter
                        total_delay = delay + jitter

                        logger.warning(
                            f"Attempt {attempt + 1} failed: {e}. Retrying in {total_delay:.2f}s..."
                        )
                        await asyncio.sleep(total_delay)
                    else:
                        logger.error(f"All {max_retries + 1} attempts failed: {e}")

            raise last_exception

        return wrapper

    return decorator


class GeminiClient:
    """Production-grade Gemini client with retries and circuit breaker."""

    def __init__(self, api_key: str, model: str = "gemini-pro"):
        self.api_key = api_key
        self.model_name = model
        self.circuit_breaker = CircuitBreaker(threshold=5, recovery_timeout=30)

        # Initialize model
        try:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel(model)
            self.is_available = True
            logger.info(f"Gemini client initialized with model: {model}")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini: {e}")
            self.model = None
            self.is_available = False

    @retry_with_backoff(max_retries=3, base_delay=1.0)
    async def generate(
        self, prompt: str, temperature: float = 0.7, max_tokens: int = 1000
    ) -> Dict[str, Any]:
        """Generate completion with full error handling."""

        # Check circuit breaker
        if not self.circuit_breaker.can_execute():
            logger.warning("Circuit breaker is open, using fallback")
            return self._create_fallback_response("Service temporarily unavailable")

        if not self.is_available or not self.model:
            logger.error("Gemini not available")
            return self._create_fallback_response("LLM service not available")

        start_time = time.time()

        try:
            # Configure generation
            generation_config = genai.types.GenerationConfig(
                temperature=temperature, max_output_tokens=max_tokens, candidate_count=1
            )

            # Generate
            response = self.model.generate_content(
                prompt, generation_config=generation_config
            )

            # Parse response
            content = response.text
            result = self._parse_response(content)

            # Record success
            self.circuit_breaker.record_success()

            # Log metrics
            latency = time.time() - start_time
            logger.info(f"Gemini request successful. Latency: {latency:.2f}s")

            return result

        except Exception as e:
            # Record failure
            self.circuit_breaker.record_failure()

            logger.error(f"Gemini generation failed: {e}")

            # Return fallback
            return self._create_fallback_response(str(e))

    def _parse_response(self, text: str) -> Dict[str, Any]:
        """Parse and validate LLM response."""
        try:
            # Extract JSON
            json_str = self._extract_json(text)
            result = json.loads(json_str)

            # Validate required fields
            required_fields = ["is_scam", "confidence"]
            for field in required_fields:
                if field not in result:
                    logger.warning(f"Missing field in response: {field}")
                    result[field] = True if field == "is_scam" else 0.7

            # Normalize fields
            result["is_scam"] = bool(result.get("is_scam", True))
            result["confidence"] = max(
                0.0, min(1.0, float(result.get("confidence", 0.7)))
            )
            result["scam_type"] = result.get("scam_type", "OTHER")
            result["threat_level"] = result.get("threat_level", "MEDIUM")
            result["reasoning"] = result.get("reasoning", "Analysis completed")
            result["persona_response"] = result.get(
                "persona_response", "I'm not sure I understand. Can you explain again?"
            )

            if "extracted_identity" not in result:
                result["extracted_identity"] = {}

            return result

        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {e}")
            return self._create_fallback_response("Failed to parse response")
        except Exception as e:
            logger.error(f"Parse error: {e}")
            return self._create_fallback_response(str(e))

    def _extract_json(self, text: str) -> str:
        """Extract JSON from text with multiple strategies."""
        # Strategy 1: Look for JSON code block
        if "```json" in text:
            start = text.find("```json") + 7
            end = text.find("```", start)
            if end > start:
                return text[start:end].strip()

        # Strategy 2: Look for any code block
        if "```" in text:
            start = text.find("```") + 3
            end = text.find("```", start)
            if end > start:
                return text[start:end].strip()

        # Strategy 3: Find JSON object
        start = text.find("{")
        end = text.rfind("}")
        if start >= 0 and end > start:
            return text[start : end + 1]

        # Strategy 4: Return as-is if it looks like JSON
        if text.strip().startswith("{") and text.strip().endswith("}"):
            return text.strip()

        return "{}"

    def _create_fallback_response(self, error_msg: str) -> Dict[str, Any]:
        """Create a safe fallback response."""
        return {
            "is_scam": True,
            "confidence": 0.6,
            "scam_type": "OTHER",
            "threat_level": "MEDIUM",
            "reasoning": f"Analysis limited due to: {error_msg}",
            "persona_response": "I'm having trouble understanding. Could you please explain that again more simply?",
            "extracted_identity": {},
            "fallback": True,
        }

    def health_check(self) -> Dict[str, Any]:
        """Check LLM service health."""
        return {
            "available": self.is_available,
            "circuit_state": self.circuit_breaker.state.state,
            "failures": self.circuit_breaker.state.failures,
            "model": self.model_name,
        }
