"""
GUVI Hackathon Callback Module

Handles the mandatory callback to GUVI evaluation endpoint
when scam engagement is complete.
"""

import httpx
import logging
from typing import List, Optional
from datetime import datetime

from .schemas import (
    GUVIFinalResultPayload,
    GUVIExtractedIntelligence,
    ExtractedIntelligence,
)

logger = logging.getLogger(__name__)

# GUVI Evaluation Endpoint
GUVI_CALLBACK_URL = "https://hackathon.guvi.in/api/updateHoneyPotFinalResult"


class GUVICallbackManager:
    """
    Manages callbacks to GUVI evaluation endpoint.
    This is MANDATORY for scoring in the hackathon.
    """

    def __init__(self):
        self.callback_url = GUVI_CALLBACK_URL
        self.timeout = 10  # seconds

    def _extract_suspicious_keywords(self, message: str) -> List[str]:
        """Extract suspicious keywords from scammer messages."""
        keywords = []
        suspicious_terms = [
            "urgent", "immediately", "verify", "blocked", "suspended",
            "arrest", "police", "cbi", "ed", "legal", "case", "warrant",
            "transfer", "payment", "account", "upi", "bank", "otp",
            "refund", "lottery", "winner", "prize", "offer", "job",
            "investment", "returns", "profit", "double", "guaranteed",
            "kyc", "update", "expire", "deadline", "fine", "penalty"
        ]
        
        message_lower = message.lower()
        for term in suspicious_terms:
            if term in message_lower:
                keywords.append(term)
        
        return keywords[:10]  # Limit to 10 keywords

    def convert_intel_to_guvi_format(
        self, intel: ExtractedIntelligence, messages: List[str]
    ) -> GUVIExtractedIntelligence:
        """Convert internal intelligence format to GUVI format."""
        # Extract suspicious keywords from all messages
        all_keywords = []
        for msg in messages:
            all_keywords.extend(self._extract_suspicious_keywords(msg))
        
        # Remove duplicates and limit
        unique_keywords = list(set(all_keywords))[:10]
        
        return GUVIExtractedIntelligence(
            bankAccounts=[acc.account_number for acc in intel.bank_accounts],
            upiIds=[upi.upi_id for upi in intel.upi_ids],
            phishingLinks=[url.url for url in intel.urls],
            phoneNumbers=[phone.number for phone in intel.phone_numbers],
            suspiciousKeywords=unique_keywords,
        )

    async def send_final_result(
        self,
        session_id: str,
        scam_detected: bool,
        total_messages: int,
        intel: ExtractedIntelligence,
        scammer_messages: List[str],
        agent_notes: str = "",
    ) -> bool:
        """
        Send final result to GUVI evaluation endpoint.
        
        This is MANDATORY for scoring. Must be called when:
        - Scam intent is confirmed (scamDetected = true)
        - AI Agent has completed sufficient engagement
        - Intelligence extraction is finished
        
        Args:
            session_id: Unique session ID from GUVI
            scam_detected: Whether scam was detected
            total_messages: Total messages exchanged
            intel: Extracted intelligence
            scammer_messages: List of scammer messages for keyword extraction
            agent_notes: Summary of scammer behavior
            
        Returns:
            True if callback was successful
        """
        try:
            # Convert intel to GUVI format
            guvi_intel = self.convert_intel_to_guvi_format(intel, scammer_messages)
            
            # Generate agent notes if not provided
            if not agent_notes:
                agent_notes = self._generate_agent_notes(intel, scammer_messages)
            
            # Build payload
            payload = GUVIFinalResultPayload(
                sessionId=session_id,
                scamDetected=scam_detected,
                totalMessagesExchanged=total_messages,
                extractedIntelligence=guvi_intel,
                agentNotes=agent_notes,
            )
            
            logger.info(f"Sending GUVI callback for session {session_id[:8]}...")
            logger.info(f"Payload: scamDetected={scam_detected}, messages={total_messages}")
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.callback_url,
                    json=payload.model_dump(),
                    timeout=self.timeout,
                    headers={
                        "Content-Type": "application/json",
                        "User-Agent": "AgenticHoneypot/2.0.0",
                    },
                )
                
                if response.status_code == 200:
                    logger.info(f"GUVI callback successful for session {session_id[:8]}")
                    return True
                else:
                    logger.warning(
                        f"GUVI callback failed with status {response.status_code}: {response.text}"
                    )
                    return False
                    
        except httpx.TimeoutException:
            logger.error(f"GUVI callback timeout for session {session_id[:8]}")
            return False
        except Exception as e:
            logger.error(f"GUVI callback error: {e}")
            return False

    def _generate_agent_notes(
        self, intel: ExtractedIntelligence, messages: List[str]
    ) -> str:
        """Generate automatic agent notes based on extracted intel."""
        notes_parts = []
        
        # Analyze scammer tactics
        all_text = " ".join(messages).lower()
        
        if any(word in all_text for word in ["arrest", "police", "cbi", "warrant"]):
            notes_parts.append("Scammer used authority impersonation tactics")
        
        if any(word in all_text for word in ["urgent", "immediately", "today", "now"]):
            notes_parts.append("Used urgency and time pressure")
        
        if any(word in all_text for word in ["blocked", "suspended", "freeze"]):
            notes_parts.append("Threatened account suspension")
        
        if intel.bank_accounts:
            notes_parts.append(f"Extracted {len(intel.bank_accounts)} bank account(s)")
        
        if intel.upi_ids:
            notes_parts.append(f"Extracted {len(intel.upi_ids)} UPI ID(s)")
        
        if intel.urls:
            notes_parts.append(f"Detected {len(intel.urls)} suspicious URL(s)")
        
        if intel.phone_numbers:
            notes_parts.append(f"Captured {len(intel.phone_numbers)} phone number(s)")
        
        if not notes_parts:
            notes_parts.append("Standard engagement completed")
        
        return ". ".join(notes_parts)


# Global instance
guvi_callback = GUVICallbackManager()
