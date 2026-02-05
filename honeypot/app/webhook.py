"""
Webhook integration for real-time intelligence alerts.
Sends extracted scam intelligence to external systems.
"""

import httpx
import logging
from typing import Dict, Any, Optional
from datetime import datetime

from .config import settings

logger = logging.getLogger(__name__)


class WebhookManager:
    """
    Manages webhook notifications for extracted intelligence.
    """

    def __init__(self):
        self.webhook_url = (
            str(settings.intel_webhook_url) if settings.intel_webhook_url else None
        )
        self.timeout = settings.webhook_timeout_seconds
        self.enabled = settings.webhook_enabled or bool(self.webhook_url)

    async def send_intel_alert(
        self,
        session_id: str,
        scam_type: str,
        threat_level: str,
        intel: Dict[str, Any],
        scammer_message: str,
    ) -> bool:
        """
        Send extracted intelligence to configured webhook.

        Args:
            session_id: Unique session identifier
            scam_type: Type of scam detected
            threat_level: Threat level (CRITICAL/HIGH/MEDIUM/LOW)
            intel: Extracted intelligence dictionary
            scammer_message: Original scammer message

        Returns:
            True if webhook sent successfully, False otherwise
        """
        if not self.enabled or not self.webhook_url:
            return False

        # Build webhook payload
        payload = {
            "timestamp": datetime.utcnow().isoformat(),
            "session_id": session_id,
            "scam_type": scam_type,
            "threat_level": threat_level,
            "scammer_message_preview": scammer_message[:200] + "..."
            if len(scammer_message) > 200
            else scammer_message,
            "extracted_intel": self._sanitize_intel(intel),
            "metadata": {
                "source": "agentic-honeypot",
                "version": "2.0.0",
                "alert_type": "real_time_extraction",
            },
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.webhook_url,
                    json=payload,
                    timeout=self.timeout,
                    headers={
                        "Content-Type": "application/json",
                        "User-Agent": "AgenticHoneypot/2.0.0",
                    },
                )

                if response.status_code == 200:
                    logger.info(
                        f"Webhook alert sent successfully for session {session_id[:8]}..."
                    )
                    return True
                else:
                    logger.warning(
                        f"Webhook returned status {response.status_code} for session {session_id[:8]}..."
                    )
                    return False

        except httpx.TimeoutException:
            logger.error(f"Webhook timeout for session {session_id[:8]}...")
            return False
        except Exception as e:
            logger.error(f"Webhook error: {e}")
            return False

    def _sanitize_intel(self, intel: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sanitize and format intelligence for webhook payload.
        Remove sensitive metadata and format for external consumption.
        """
        sanitized = {}

        # Extract bank accounts
        if intel.get("bank_accounts"):
            sanitized["bank_accounts"] = [
                {
                    "account_number": acc.get("account_number", ""),
                    "ifsc_code": acc.get("ifsc_code", ""),
                    "bank_name": acc.get("bank_name", ""),
                    "confidence": acc.get("confidence", 0.0),
                }
                for acc in intel["bank_accounts"]
            ]

        # Extract UPI IDs
        if intel.get("upi_ids"):
            sanitized["upi_ids"] = [
                {
                    "upi_id": upi.get("upi_id", ""),
                    "confidence": upi.get("confidence", 0.0),
                }
                for upi in intel["upi_ids"]
            ]

        # Extract phone numbers
        if intel.get("phone_numbers"):
            sanitized["phone_numbers"] = [
                {
                    "number": phone.get("number", ""),
                    "confidence": phone.get("confidence", 0.0),
                }
                for phone in intel["phone_numbers"]
            ]

        # Extract URLs
        if intel.get("urls"):
            sanitized["urls"] = [
                {
                    "url": url.get("url", ""),
                    "domain": url.get("domain", ""),
                    "risk_score": url.get("risk_score", 0.0),
                    "impersonating": url.get("impersonating"),
                }
                for url in intel["urls"]
            ]

        # Extract emails
        if intel.get("emails"):
            sanitized["emails"] = [
                {
                    "email": email.get("email", ""),
                    "confidence": email.get("confidence", 0.0),
                }
                for email in intel["emails"]
            ]

        # Extract crypto wallets
        if intel.get("crypto_wallets"):
            sanitized["crypto_wallets"] = [
                {
                    "address": wallet.get("address", ""),
                    "currency": wallet.get("currency", ""),
                    "confidence": wallet.get("confidence", 0.0),
                }
                for wallet in intel["crypto_wallets"]
            ]

        # Extract scammer identity
        if intel.get("scammer_identity"):
            identity = intel["scammer_identity"]
            sanitized["scammer_identity"] = {
                "claimed_name": identity.get("claimed_name"),
                "claimed_organization": identity.get("claimed_organization"),
                "claimed_designation": identity.get("claimed_designation"),
                "impersonation_type": identity.get("impersonation_type"),
            }

        return sanitized

    async def send_batch_alert(
        self, session_id: str, total_intel_count: int, session_summary: Dict[str, Any]
    ) -> bool:
        """
        Send summary alert when session ends or significant intel collected.

        Args:
            session_id: Session identifier
            total_intel_count: Total number of intel items extracted
            session_summary: Summary of the entire session

        Returns:
            True if sent successfully
        """
        if not self.enabled or not self.webhook_url:
            return False

        payload = {
            "timestamp": datetime.utcnow().isoformat(),
            "session_id": session_id,
            "alert_type": "session_summary",
            "total_intel_extracted": total_intel_count,
            "session_summary": session_summary,
            "metadata": {"source": "agentic-honeypot", "version": "2.0.0"},
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.webhook_url, json=payload, timeout=self.timeout
                )
                return response.status_code == 200
        except Exception as e:
            logger.error(f"Batch webhook error: {e}")
            return False


# Global webhook manager instance
webhook_manager = WebhookManager()
