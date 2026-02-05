from fastapi import FastAPI, Request, BackgroundTasks
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
import time
import random
import asyncio
import logging
import re
import uuid
from datetime import datetime
from typing import Dict, Optional, List

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

from .schemas import *
from .extraction import AdvancedExtractionEngine
from .llm_client import GeminiClient
from .personas import persona_manager, AdvancedPersona, EmotionalState
from .schemas import ThreatLevel, GUVIRequest, GUVIResponse, GUVIMessage
from .config import settings
from .utils import rate_limiter, session_manager
from .webhook import webhook_manager
from .guvi_callback import guvi_callback

app = FastAPI(
    title="Agentic Honeypot API",
    version="2.0.0",
    description="Advanced AI-powered scam detection and engagement system",
)

# Middleware
app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://huggingface.co",
        "https://*.hf.space",
        "https://hackathon.guvi.in",  # GUVI Hackathon
        "https://*.guvi.in",  # GUVI domains
        "http://localhost:3000",  # For local development
        "http://localhost:8000",  # For local development
    ],
    allow_methods=["GET", "POST"],
    allow_headers=["X-API-Key", "x-api-key", "Content-Type", "Authorization"],
    max_age=600,  # Cache preflight requests for 10 minutes
)

# Initialize components
extraction_engine = AdvancedExtractionEngine()
llm_client = GeminiClient(settings.gemini_api_key) if settings.gemini_api_key else None

# Persona instances storage
persona_instances: dict = {}

# Analytics storage
analytics = {
    "total_requests": 0,
    "scam_detected": 0,
    "safe_messages": 0,
    "avg_response_time": 0.0,
    "error_count": 0,
}


def update_analytics(response_time: float, is_scam: bool, is_error: bool = False):
    """Update analytics metrics."""
    analytics["total_requests"] += 1
    if is_error:
        analytics["error_count"] += 1
    elif is_scam:
        analytics["scam_detected"] += 1
    else:
        analytics["safe_messages"] += 1

    # Update rolling average
    n = analytics["total_requests"]
    analytics["avg_response_time"] = float(
        (analytics["avg_response_time"] * (n - 1) + response_time) / n
    )


# Authentication & Rate Limiting middleware
@app.middleware("http")
async def auth_and_rate_limit_middleware(request: Request, call_next):
    # Skip auth for health and metrics
    if request.url.path in ["/health", "/metrics", "/docs", "/openapi.json"]:
        return await call_next(request)

    api_key = request.headers.get("X-API-Key")

    if not api_key:
        return JSONResponse(
            status_code=401,
            content={
                "error": {
                    "code": "AUTH_MISSING",
                    "message": "API key is required. Include X-API-Key header.",
                    "timestamp": datetime.utcnow().isoformat(),
                }
            },
        )

    if api_key != settings.api_key:
        return JSONResponse(
            status_code=403,
            content={
                "error": {
                    "code": "AUTH_INVALID",
                    "message": "Invalid API key provided.",
                    "timestamp": datetime.utcnow().isoformat(),
                }
            },
        )

    # Rate limiting check
    if not rate_limiter.is_allowed(api_key):
        retry_after = rate_limiter.get_retry_after(api_key)
        return JSONResponse(
            status_code=429,
            content={
                "error": {
                    "code": "RATE_LIMITED",
                    "message": f"Rate limit exceeded. Try again in {retry_after} seconds.",
                    "retry_after": retry_after,
                    "timestamp": datetime.utcnow().isoformat(),
                }
            },
        )


# Anti-detection: typing delay calculator
def calculate_typing_delay(message: str, persona: AdvancedPersona) -> float:
    """Calculate realistic typing delay based on message and persona."""
    # Allow disabling delays for evaluation mode
    if settings.disable_delays:
        return 0.0

    base_delay = 0.3  # Reduced from 0.5

    # Length-based delay (longer messages take more time)
    # Cap message length at 500 chars to prevent excessive delays
    effective_length = min(len(message), 500)
    char_delay = effective_length * 0.005  # 5ms per character (reduced from 30ms)

    # Persona adjustment (older = slower)
    age_factor = 1.0
    if persona.age > 60:
        age_factor = 1.2  # Reduced from 1.5
    elif persona.age < 30:
        age_factor = 0.9  # Increased from 0.8

    # Tech literacy adjustment
    tech_factor = 1.0
    if persona.tech_literacy == "low":
        tech_factor = 1.15  # Reduced from 1.3
    elif persona.tech_literacy == "high":
        tech_factor = 0.95  # Increased from 0.9

    # Emotional state adjustment
    emotion_factor = 1.0
    if persona.state.current_emotion in [
        EmotionalState.SCARED,
        EmotionalState.PANICKED,
    ]:
        emotion_factor = 0.85  # Less speedup when scared
    elif persona.state.current_emotion == EmotionalState.CONFUSED:
        emotion_factor = 1.2  # Reduced slowdown when confused

    total_delay = (base_delay + char_delay) * age_factor * tech_factor * emotion_factor

    # Add randomness (±15% instead of ±20%)
    jitter = random.uniform(-0.15, 0.15)
    total_delay = total_delay * (1 + jitter)

    return max(
        0.1, min(total_delay, 1.0)
    )  # Cap between 0.1s and 1.0s (reduced from 4.0s)


# Anti-detection: typo injection
def add_realistic_typos(text: str, persona: AdvancedPersona) -> str:
    """Add realistic typos to text based on persona."""
    # Skip for short text
    if len(text) < 10:
        return text

    # Lower typo rate for high-literacy personas
    base_typo_rate = 0.08  # 8% base rate
    if persona.tech_literacy == "high":
        typo_rate = 0.04
    elif persona.tech_literacy == "medium":
        typo_rate = 0.06
    else:
        typo_rate = base_typo_rate

    # Higher typo rate when anxious/scared
    if persona.state.current_emotion in [EmotionalState.ANXIOUS, EmotionalState.SCARED]:
        typo_rate += 0.03

    if random.random() > typo_rate:
        return text

    words = text.split()
    if len(words) < 3:
        return text

    # Common typo patterns
    typo_patterns = [
        (r"the\b", "teh"),
        (r"and\b", "adn"),
        (r"you\b", "yuo"),
        (r"your\b", "youre"),
        (r"sir\b", "sri"),
        (r"account\b", "acount"),
        (r"please\b", "plz"),
        (r"thank\b", "thnk"),
        (r"what\b", "wat"),
        (r"this\b", "tis"),
    ]

    # Pick a word to typo
    attempts = 0
    while attempts < 5:
        idx = random.randint(0, min(len(words) - 1, 8))  # Bias toward beginning
        word = words[idx].lower()

        for pattern, typo in typo_patterns:
            if re.search(pattern, word):
                words[idx] = re.sub(pattern, typo, word, count=1)

                # Add self-correction sometimes (30% chance)
                if random.random() < 0.3 and idx < len(words) - 1:
                    words.insert(idx + 1, f"*{words[idx]}*")

                return " ".join(words)

        attempts += 1

    # Fallback: swap adjacent characters
    if len(words) > 3:
        idx = random.randint(1, min(len(words) - 2, 5))
        word = list(words[idx])
        if len(word) > 3:
            pos = random.randint(0, len(word) - 2)
            word[pos], word[pos + 1] = word[pos + 1], word[pos]
            words[idx] = "".join(word)

    return " ".join(words)


def self_correct_response(response: str, persona: AdvancedPersona) -> tuple[str, bool]:
    """
    Self-correction filter to catch AI-exposure phrases and persona breaks.
    Returns: (corrected_response, was_corrected)
    """
    if not response:
        return response, False

    was_corrected = False
    corrected = response

    # AI exposure phrases to remove/replace
    ai_exposure_phrases = {
        "as an ai": "",
        "as a language model": "",
        "i'm an ai": "",
        "i am an ai": "",
        "i cannot": "main nahi kar sakti",
        "i can't": "main nahi kar sakti",
        "i'm programmed": "",
        "i am programmed": "",
        "i don't have feelings": "",
        "i don't have emotions": "",
        "i'm just a": "main bas ek",
        "i am designed to": "",
        "my programming": "",
        "my training": "",
        "artificial intelligence": "",
        "language model": "",
        "algorithm": "tarika",
        "processing": "soch rahi hoon",
        "computing": "",
        "database": "records",
        "system": "vyavastha",
    }

    response_lower = response.lower()

    # Check for AI exposure phrases
    for phrase, replacement in ai_exposure_phrases.items():
        if phrase in response_lower:
            if replacement:
                # Replace with persona-appropriate alternative
                corrected = re.sub(
                    re.escape(phrase), replacement, corrected, flags=re.IGNORECASE
                )
            else:
                # Remove entirely
                corrected = re.sub(
                    re.escape(phrase), "", corrected, flags=re.IGNORECASE
                )
            was_corrected = True
            logger.warning(f"Self-correction applied: Removed AI phrase '{phrase}'")

    # Persona consistency checks
    if persona.tech_literacy == "low":
        # Remove technical jargon for low-tech personas
        technical_terms = {
            "api": "system",
            "database": "records",
            "algorithm": "hisab",
            "encryption": "suraksha",
            "verify": "check",
            "authentication": "pehchan",
            "transaction id": "reference number",
            "otp": "code",
        }

        for term, simple_word in technical_terms.items():
            if term in corrected.lower():
                corrected = re.sub(
                    re.escape(term), simple_word, corrected, flags=re.IGNORECASE
                )
                was_corrected = True

    # Clean up any double spaces or leading/trailing issues
    corrected = re.sub(r"\s+", " ", corrected).strip()

    return corrected, was_corrected


# Persona selection logic
def select_persona_with_strategy(
    scam_type: str, message: str, turn: int
) -> AdvancedPersona:
    """Select persona with advanced strategy."""
    persona = persona_manager.select_persona(scam_type, message)

    # Initialize state based on message urgency
    is_threat = any(
        word in message.lower()
        for word in ["arrest", "jail", "police", "legal", "case"]
    )
    persona.state.evolve(message, is_threat)

    # Add initial facts to memory
    persona.memory.add_fact("name", persona.name)
    persona.memory.add_fact("location", persona.location)
    persona.memory.add_fact("occupation", persona.occupation)

    return persona


# Create comprehensive prompt
def create_master_prompt(
    message: str, persona: AdvancedPersona, history: List[Dict], turn: int
) -> str:
    """Create comprehensive prompt for LLM."""

    # Get persona's system prompt
    base_prompt = persona.get_system_prompt(history, turn)

    # Get recent conversation context
    recent_history = history[-5:] if len(history) > 5 else history
    history_text = (
        "\n".join(
            [f"{h['role'].upper()}: {h['content'][:150]}..." for h in recent_history]
        )
        if recent_history
        else "No previous conversation."
    )

    # Get memory context
    memory_text = persona.memory.recall_recent(3)

    comprehensive_prompt = f"""{base_prompt}

CONVERSATION HISTORY:
{history_text}

CURRENT SCAMMER MESSAGE:
"{message}"

YOUR TASK:
1. Analyze if this is a scam message (look for urgency, threats, impersonation, financial demands)
2. Classify the exact scam type
3. Respond naturally as {persona.name} would - stay completely in character
4. Extract any names, organizations, or claimed identities mentioned

RESPONSE GUIDELINES:
- Sound like a real {persona.age}-year-old {persona.occupation} from {persona.location}
- Show emotion appropriate to the situation
- Ask questions to get more information
- Never reveal you're an AI or automated system
- Use natural language with occasional hesitation
- Reference previous conversation details occasionally (2-3 times per session)
- If asked about being a bot/AI, get offended or confused

MEMORY RECALL - USE THESE PHRASES NATURALLY:
- "You said your name was [name], right?"
- "Earlier you mentioned [detail]..."
- "Wait, before you said [X], now you're saying [Y]?"
- "My son told me to ask about this when you called..."
- "I remember you said [detail] in your first message..."

Make the conversation feel continuous and human.

OUTPUT (JSON format):
{{
  "is_scam": true/false,
  "confidence": 0.0-1.0,
  "scam_type": "DIGITAL_ARREST/UPI_FRAUD/JOB_SCAM/INVESTMENT_SCAM/LOTTERY/PHISHING/OTHER/NONE",
  "threat_level": "CRITICAL/HIGH/MEDIUM/LOW/NONE",
  "reasoning": "Brief analysis of why this is/isn't a scam",
  "persona_response": "Your natural response as the persona (2-4 sentences)",
  "extracted_identity": {{
    "name": "scammer's claimed name or null",
    "organization": "claimed organization or null",
    "designation": "claimed role/title or null"
  }}
}}

Remember: You are a real person, not an AI. Respond naturally!"""

    return comprehensive_prompt


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "agentic-honeypot",
        "version": "2.0.0",
        "timestamp": datetime.utcnow().isoformat(),
        "llm_available": llm_client.is_available if llm_client else False,
        "llm_health": llm_client.health_check() if llm_client else {"available": False},
        "environment": "production",
        "webhook_enabled": webhook_manager.enabled,
        "webhook_configured": bool(webhook_manager.webhook_url),
    }


@app.get("/metrics")
async def get_metrics():
    """Get service metrics."""
    return {
        "analytics": analytics,
        "active_sessions": session_manager.get_stats()["total_sessions"],
        "active_personas": len(persona_instances),
        "timestamp": datetime.utcnow().isoformat(),
    }


@app.post("/api/v1/honeypot", response_model=HoneypotResponse)
async def honeypot_endpoint(
    request: HoneypotRequest, background_tasks: BackgroundTasks
):
    """Main honeypot endpoint with advanced features."""
    start_time = time.time()

    try:
        # Create or load session using session manager
        session_id, session, is_new_session = session_manager.get_or_create(
            request.session_id
        )
        persona = persona_instances.get(session_id) if not is_new_session else None

        # Select or retrieve persona
        if persona is None:
            # Determine likely scam type for initial selection
            temp_extraction = extraction_engine.extract_all(request.message)
            initial_scam_type = "OTHER"

            if temp_extraction.scammer_identity:
                org = temp_extraction.scammer_identity.claimed_organization
                if org and any(
                    x in org.lower() for x in ["cbi", "police", "income tax", "ed"]
                ):
                    initial_scam_type = "DIGITAL_ARREST"
                elif org and any(
                    x in org.lower() for x in ["paytm", "phonepe", "bank"]
                ):
                    initial_scam_type = "UPI_FRAUD"

            persona = select_persona_with_strategy(
                initial_scam_type, request.message, 0
            )
            persona_instances[session_id] = persona

        # Update session history
        session["history"].append({"role": "scammer", "content": request.message})

        # Get conversation history
        history = session["history"] + (request.conversation_history or [])

        # Calculate typing delay (anti-detection)
        typing_delay = calculate_typing_delay(request.message, persona)
        await asyncio.sleep(typing_delay)

        # Get LLM response
        llm_result = {}
        if llm_client and llm_client.is_available:
            prompt = create_master_prompt(
                request.message, persona, history, session["turns"]
            )
            llm_result = await llm_client.generate(prompt)
        else:
            # Enhanced fallback without LLM
            is_scam = any(
                word in request.message.lower()
                for word in [
                    "cbi",
                    "police",
                    "arrest",
                    "account",
                    "transfer",
                    "paytm",
                    "upi",
                ]
            )
            llm_result = {
                "is_scam": is_scam,
                "confidence": 0.7 if is_scam else 0.3,
                "scam_type": "DIGITAL_ARREST"
                if "cbi" in request.message.lower()
                or "police" in request.message.lower()
                else "OTHER",
                "threat_level": "HIGH" if is_scam else "LOW",
                "reasoning": "Pattern-based detection (LLM unavailable)",
                "persona_response": "Arre bhaiya, main samajh nahi pa raha. Aap phir se batao?",
                "extracted_identity": {},
            }

        # Update persona state based on scam detection
        if llm_result.get("is_scam"):
            is_threat = llm_result.get("threat_level") in ["CRITICAL", "HIGH"]
            persona.state.evolve(request.message, is_threat)

        # Extract intelligence with advanced engine
        regex_intel = extraction_engine.extract_all(request.message)

        # Merge LLM identity extraction
        if llm_result.get("extracted_identity"):
            identity_data = llm_result["extracted_identity"]
            if not regex_intel.scammer_identity:
                regex_intel.scammer_identity = ScammerIdentity()

            if identity_data.get("name"):
                regex_intel.scammer_identity.claimed_name = identity_data["name"]
            if identity_data.get("organization"):
                regex_intel.scammer_identity.claimed_organization = identity_data[
                    "organization"
                ]
            if identity_data.get("designation"):
                regex_intel.scammer_identity.claimed_designation = identity_data[
                    "designation"
                ]

        # Update persona memory with extracted intel
        if regex_intel.scammer_identity:
            if regex_intel.scammer_identity.claimed_name:
                persona.memory.add_fact(
                    "scammer_name", regex_intel.scammer_identity.claimed_name
                )
            if regex_intel.scammer_identity.claimed_organization:
                persona.memory.add_fact(
                    "claimed_org", regex_intel.scammer_identity.claimed_organization
                )

        # Send webhook alert if intel extracted and webhook configured
        # This happens in background to not block response
        if llm_result.get("is_scam"):
            intel_count = (
                len(regex_intel.bank_accounts)
                + len(regex_intel.upi_ids)
                + len(regex_intel.phone_numbers)
                + len(regex_intel.urls)
                + len(regex_intel.emails)
                + len(regex_intel.crypto_wallets)
            )

            if intel_count > 0:
                # Fire and forget webhook call (don't await)
                asyncio.create_task(
                    webhook_manager.send_intel_alert(
                        session_id=session_id,
                        scam_type=llm_result.get("scam_type", "OTHER"),
                        threat_level=llm_result.get("threat_level", "MEDIUM"),
                        intel=regex_intel.model_dump(),
                        scammer_message=request.message,
                    )
                )

        # Get persona response, apply self-correction, and add typos
        persona_response = llm_result.get("persona_response", "")
        self_correction_applied = False

        if persona_response and llm_result.get("is_scam"):
            # Apply self-correction filter first
            persona_response, self_correction_applied = self_correct_response(
                persona_response, persona
            )
            # Then add realistic typos
            persona_response = add_realistic_typos(persona_response, persona)

        # Update session
        session["turns"] += 1
        if persona_response:
            session["history"].append({"role": "honeypot", "content": persona_response})

        # Track collected intel
        intel_list = []
        if regex_intel.bank_accounts:
            intel_list.append("bank_account")
        if regex_intel.upi_ids:
            intel_list.append("upi_id")
        if regex_intel.phone_numbers:
            intel_list.append("phone_number")
        if regex_intel.urls:
            intel_list.append("url")
        if regex_intel.emails:
            intel_list.append("email")
        if regex_intel.crypto_wallets:
            intel_list.append("crypto_wallet")
        if regex_intel.scammer_identity:
            intel_list.append("scammer_identity")

        # Count memory recall events (references to previous conversation)
        memory_recall_events = 0
        if persona_response:
            recall_indicators = [
                "you said",
                "you mentioned",
                "earlier",
                "before",
                "last time",
                "previously",
                "you told",
                "you asked",
            ]
            response_lower = persona_response.lower()
            for indicator in recall_indicators:
                if indicator in response_lower:
                    memory_recall_events += 1

        # Track emotional state transitions (use turn count as proxy)
        emotional_transitions = min(persona.state.turn_count, 5)

        session["intel_collected"] = list(
            set(session.get("intel_collected", []) + intel_list)
        )

        # Save session using manager
        session_manager.update(
            session_id,
            {
                "turns": session["turns"],
                "history": session["history"],
                "intel_collected": session["intel_collected"],
            },
        )

        # Calculate metrics
        response_time = time.time() - start_time

        # Update analytics in background
        background_tasks.add_task(
            update_analytics,
            response_time,
            llm_result.get("is_scam", False),
            llm_result.get("fallback", False),
        )

        # Convert threat_level string to enum
        threat_level_str = llm_result.get("threat_level", "MEDIUM")
        try:
            threat_level = ThreatLevel(threat_level_str)
        except ValueError:
            threat_level = ThreatLevel.MEDIUM

        # Build response
        return HoneypotResponse(
            session_id=session_id,
            timestamp=datetime.utcnow().isoformat(),
            scam_detection=ScamDetection(
                is_scam=llm_result.get("is_scam", True),
                confidence=llm_result.get("confidence", 0.7),
                scam_type=llm_result.get("scam_type"),
                threat_level=threat_level,
                reasoning=llm_result.get("reasoning", "Analysis completed"),
            ),
            honeypot_response=PersonaResponse(
                message=persona_response if llm_result.get("is_scam") else None,
                persona_used=persona.id,
                strategy="ADAPTIVE_ENGAGEMENT",
            ),
            extracted_intelligence=regex_intel,
            engagement_metrics=EngagementMetrics(
                turn_number=session["turns"],
                total_turns=session["turns"],
                response_time_ms=int(response_time * 1000),
                engagement_duration_seconds=int(response_time),
                memory_recall_events=memory_recall_events,
                self_corrections_applied=int(self_correction_applied),
                emotional_state_transitions=emotional_transitions,
                persona_consistency_score=0.85 if not self_correction_applied else 0.75,
                response_naturalness=0.80 + (0.05 * memory_recall_events),
            ),
            conversation_state=ConversationState(
                status="ACTIVE" if llm_result.get("is_scam") else "SAFE",
                intel_collected=intel_list,
                intel_pending=[],
            ),
        )

    except Exception as e:
        logger.error(f"Error processing request: {e}", exc_info=True)

        # Update analytics
        update_analytics(time.time() - start_time, False, True)

        # Return error response
        return HoneypotResponse(
            session_id=str(uuid.uuid4()),
            timestamp=datetime.utcnow().isoformat(),
            scam_detection=ScamDetection(
                is_scam=False,
                confidence=0.0,
                scam_type=None,
                threat_level=ThreatLevel.NONE,  # Use enum consistently
                reasoning="An internal error occurred while processing your request. Please try again.",
            ),
            honeypot_response=PersonaResponse(
                message=None, persona_used=None, strategy=None
            ),
            extracted_intelligence=ExtractedIntelligence(),
            engagement_metrics=EngagementMetrics(
                turn_number=0,
                total_turns=0,
                response_time_ms=int((time.time() - start_time) * 1000),
                engagement_duration_seconds=0,
                memory_recall_events=0,
                self_corrections_applied=0,
                emotional_state_transitions=0,
                persona_consistency_score=0.0,
                response_naturalness=0.0,
            ),
            conversation_state=ConversationState(
                status="ERROR", intel_collected=[], intel_pending=[]
            ),
        )


@app.get("/")
async def root():
    """Root endpoint with API info."""
    return {
        "service": "Agentic Honeypot API",
        "version": "2.0.0",
        "description": "Advanced AI-powered scam detection and engagement",
        "endpoints": {
            "honeypot": "/api/v1/honeypot",
            "guvi_honeypot": "/api/v1/guvi-honeypot",
            "health": "/health",
            "metrics": "/metrics",
            "docs": "/docs",
        },
        "features": [
            "Multi-language support (Hindi/English/Hinglish)",
            "8 dynamic personas with memory",
            "Advanced intelligence extraction",
            "Anti-detection measures",
            "Real-time analytics",
            "GUVI Hackathon Compatible",
        ],
    }


# ============================================================
# GUVI HACKATHON COMPATIBLE ENDPOINT
# This endpoint matches the official GUVI API specification exactly
# ============================================================


@app.post("/api/v1/guvi-honeypot", response_model=GUVIResponse)
async def guvi_honeypot_endpoint(
    request: GUVIRequest, background_tasks: BackgroundTasks
):
    """
    GUVI Hackathon compatible endpoint.
    
    Accepts the official GUVI request format and returns simplified response.
    Also handles mandatory callback to GUVI evaluation endpoint.
    """
    start_time = time.time()
    
    try:
        # Extract message text from GUVI format
        message_text = request.message.text
        session_id = request.sessionId
        
        # Convert GUVI conversation history to internal format
        internal_history = []
        for msg in request.conversationHistory:
            internal_history.append({
                "role": "scammer" if msg.sender == "scammer" else "honeypot",
                "content": msg.text,
            })
        
        # Get or create session
        _, session, is_new_session = session_manager.get_or_create(session_id)
        persona = persona_instances.get(session_id) if not is_new_session else None
        
        # Select or retrieve persona
        if persona is None:
            temp_extraction = extraction_engine.extract_all(message_text)
            initial_scam_type = "OTHER"
            
            if temp_extraction.scammer_identity:
                org = temp_extraction.scammer_identity.claimed_organization
                if org and any(
                    x in org.lower() for x in ["cbi", "police", "income tax", "ed"]
                ):
                    initial_scam_type = "DIGITAL_ARREST"
                elif org and any(
                    x in org.lower() for x in ["paytm", "phonepe", "bank"]
                ):
                    initial_scam_type = "UPI_FRAUD"
            
            persona = select_persona_with_strategy(initial_scam_type, message_text, 0)
            persona_instances[session_id] = persona
        
        # Update session history
        session["history"].append({"role": "scammer", "content": message_text})
        
        # Get full history
        history = session["history"] + internal_history
        
        # Calculate typing delay (anti-detection)
        typing_delay = calculate_typing_delay(message_text, persona)
        await asyncio.sleep(typing_delay)
        
        # Get LLM response
        llm_result = {}
        if llm_client and llm_client.is_available:
            prompt = create_master_prompt(message_text, persona, history, session["turns"])
            llm_result = await llm_client.generate(prompt)
        else:
            # Fallback without LLM
            is_scam = any(
                word in message_text.lower()
                for word in ["cbi", "police", "arrest", "account", "transfer", "paytm", "upi"]
            )
            llm_result = {
                "is_scam": is_scam,
                "confidence": 0.7 if is_scam else 0.3,
                "scam_type": "DIGITAL_ARREST" if "cbi" in message_text.lower() else "OTHER",
                "threat_level": "HIGH" if is_scam else "LOW",
                "reasoning": "Pattern-based detection",
                "persona_response": "Arre bhaiya, main samajh nahi pa raha. Aap phir se batao?",
                "extracted_identity": {},
            }
        
        # Update persona state
        if llm_result.get("is_scam"):
            is_threat = llm_result.get("threat_level") in ["CRITICAL", "HIGH"]
            persona.state.evolve(message_text, is_threat)
        
        # Extract intelligence
        regex_intel = extraction_engine.extract_all(message_text)
        
        # Get persona response and apply self-correction
        persona_response = llm_result.get("persona_response", "")
        if persona_response and llm_result.get("is_scam"):
            persona_response, _ = self_correct_response(persona_response, persona)
            persona_response = add_realistic_typos(persona_response, persona)
        
        # Update session
        session["turns"] += 1
        if persona_response:
            session["history"].append({"role": "honeypot", "content": persona_response})
        
        # Collect scammer messages for keyword extraction
        scammer_messages = [
            h["content"] for h in session["history"] if h.get("role") == "scammer"
        ]
        
        # Save session
        session_manager.update(
            session_id,
            {
                "turns": session["turns"],
                "history": session["history"],
                "intel": regex_intel,
            },
        )
        
        # Send GUVI callback in background (mandatory for scoring)
        # This is triggered when we have enough engagement or intel
        if llm_result.get("is_scam") and session["turns"] >= 2:
            intel_count = (
                len(regex_intel.bank_accounts)
                + len(regex_intel.upi_ids)
                + len(regex_intel.phone_numbers)
                + len(regex_intel.urls)
            )
            
            # Send callback if we have intel or reached 5+ turns
            if intel_count > 0 or session["turns"] >= 5:
                background_tasks.add_task(
                    guvi_callback.send_final_result,
                    session_id=session_id,
                    scam_detected=True,
                    total_messages=session["turns"],
                    intel=regex_intel,
                    scammer_messages=scammer_messages,
                    agent_notes="",
                )
        
        # Update analytics
        response_time = time.time() - start_time
        background_tasks.add_task(
            update_analytics,
            response_time,
            llm_result.get("is_scam", False),
            False,
        )
        
        # Return GUVI-compatible response
        return GUVIResponse(
            status="success",
            reply=persona_response if persona_response else "Hello?",
        )
        
    except Exception as e:
        logger.error(f"GUVI endpoint error: {e}", exc_info=True)
        return GUVIResponse(
            status="error",
            reply="Sorry, I didn't understand. Can you repeat?",
        )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=settings.port)
