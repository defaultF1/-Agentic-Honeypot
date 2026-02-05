from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from enum import Enum


class ScamType(str, Enum):
    DIGITAL_ARREST = "DIGITAL_ARREST"
    UPI_FRAUD = "UPI_FRAUD"
    JOB_SCAM = "JOB_SCAM"
    INVESTMENT_SCAM = "INVESTMENT_SCAM"
    LOTTERY = "LOTTERY"
    PHISHING = "PHISHING"
    OTHER = "OTHER"
    NONE = "NONE"


class ThreatLevel(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    NONE = "NONE"


class MessageTurn(BaseModel):
    role: str = Field(..., pattern="^(scammer|honeypot)$")
    content: str
    timestamp: Optional[str] = None


class HoneypotRequest(BaseModel):
    session_id: Optional[str] = None
    message: str = Field(
        ...,
        min_length=1,
        max_length=5000,
        description="Scam message to analyze (max 5000 characters)",
    )
    conversation_history: Optional[List[MessageTurn]] = []


class BankAccount(BaseModel):
    account_number: str
    ifsc_code: Optional[str] = None
    bank_name: Optional[str] = None
    confidence: float = Field(..., ge=0.0, le=1.0)


class UPIID(BaseModel):
    upi_id: str
    confidence: float = Field(..., ge=0.0, le=1.0)


class PhoneNumber(BaseModel):
    number: str
    confidence: float = Field(..., ge=0.0, le=1.0)


class URL(BaseModel):
    url: str
    domain: str
    risk_score: float = Field(default=0.5, ge=0.0, le=1.0)
    impersonating: Optional[str] = None
    is_active: bool = True


class Email(BaseModel):
    email: str
    confidence: float = Field(..., ge=0.0, le=1.0)


class CryptoWallet(BaseModel):
    address: str
    currency: str  # "BTC", "ETH", "USDT", etc.
    confidence: float = Field(..., ge=0.0, le=1.0)


class ScammerIdentity(BaseModel):
    claimed_name: Optional[str] = None
    claimed_organization: Optional[str] = None
    claimed_designation: Optional[str] = None
    impersonation_type: Optional[str] = None


class ExtractedIntelligence(BaseModel):
    bank_accounts: List[BankAccount] = []
    upi_ids: List[UPIID] = []
    phone_numbers: List[PhoneNumber] = []
    urls: List[URL] = []
    emails: List[Email] = []
    crypto_wallets: List[CryptoWallet] = []
    scammer_identity: Optional[ScammerIdentity] = None


class ScamDetection(BaseModel):
    is_scam: bool
    confidence: float = Field(..., ge=0.0, le=1.0)
    scam_type: Optional[ScamType] = None
    threat_level: ThreatLevel = ThreatLevel.NONE
    reasoning: str


class PersonaResponse(BaseModel):
    message: Optional[str] = None
    persona_used: Optional[str] = None
    strategy: Optional[str] = None


class EngagementMetrics(BaseModel):
    turn_number: int = 1
    total_turns: int = 1
    response_time_ms: int = 0
    engagement_duration_seconds: int = 0
    memory_recall_events: int = 0
    self_corrections_applied: int = 0
    emotional_state_transitions: int = 0
    persona_consistency_score: float = Field(default=0.85, ge=0.0, le=1.0)
    response_naturalness: float = Field(default=0.80, ge=0.0, le=1.0)


class ConversationState(BaseModel):
    status: str = "ACTIVE"
    intel_collected: List[str] = []
    intel_pending: List[str] = []


class HoneypotResponse(BaseModel):
    session_id: str
    timestamp: str
    scam_detection: ScamDetection
    honeypot_response: PersonaResponse
    extracted_intelligence: ExtractedIntelligence
    engagement_metrics: EngagementMetrics
    conversation_state: ConversationState


# ============================================================
# GUVI HACKATHON COMPATIBLE SCHEMAS
# These match the official GUVI API specification exactly
# ============================================================


class GUVIMessage(BaseModel):
    """GUVI format message with sender, text, and timestamp."""
    sender: str  # "scammer" or "user"
    text: str
    timestamp: int  # Epoch time in milliseconds


class GUVIMetadata(BaseModel):
    """GUVI format metadata."""
    channel: str = "SMS"  # SMS, WhatsApp, Email, Chat
    language: str = "English"
    locale: str = "IN"


class GUVIRequest(BaseModel):
    """GUVI hackathon request format - matches official spec exactly."""
    sessionId: str
    message: GUVIMessage
    conversationHistory: List[GUVIMessage] = []
    metadata: Optional[GUVIMetadata] = None

    class Config:
        populate_by_name = True


class GUVIResponse(BaseModel):
    """GUVI hackathon response format - simple status and reply."""
    status: str  # "success" or "error"
    reply: str  # Agent's response message


class GUVIExtractedIntelligence(BaseModel):
    """GUVI format for extracted intelligence callback."""
    bankAccounts: List[str] = []
    upiIds: List[str] = []
    phishingLinks: List[str] = []
    phoneNumbers: List[str] = []
    suspiciousKeywords: List[str] = []


class GUVIFinalResultPayload(BaseModel):
    """Payload for mandatory GUVI callback endpoint."""
    sessionId: str
    scamDetected: bool
    totalMessagesExchanged: int
    extractedIntelligence: GUVIExtractedIntelligence
    agentNotes: str
