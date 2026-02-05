# 🛡️ Agentic Honeypot Implementation Plan
## Free, Fast, Python 3.12 + HF Spaces

**Version:** 1.0  
**Date:** 2026-02-05  
**Status:** Ready for Implementation  

---

## 📋 Executive Summary

This implementation plan provides a **100% free, no-credit-card-required** solution for building an Agentic Honeypot that complies with GUVI's evaluation requirements. The system uses:

- **Python 3.12** (latest stable)
- **FastAPI** for the REST API
- **Hugging Face Spaces** for hosting (fastest free option)
- **In-memory sessions** (no database needed)
- **OpenAI-compatible LLM adapter** (waiting for provider selection)

**Key Compliance Points:**
- ✅ Single public API endpoint
- ✅ API key authentication (X-API-Key header)
- ✅ JSON response format as specified
- ✅ Scam detection + persona engagement + intelligence extraction
- ✅ Handles concurrent requests
- ✅ < 3 second response time target

---

## 🎯 Tech Stack Overview

| Component | Technology | Cost | Notes |
|-----------|------------|------|-------|
| **Language** | Python 3.12 | Free | Latest stable version |
| **Framework** | FastAPI + Uvicorn | Free | Async, auto-docs, OpenAPI |
| **Hosting** | Hugging Face Spaces | Free | No cold starts, 16GB RAM, 2 vCPU |
| **LLM** | **TBD by user** | Free tier | Groq / OpenRouter / HF Inference |
| **Storage** | In-memory dict + Lock | Free | No database needed for evaluation |
| **HTTP Client** | httpx (async) | Free | For LLM API calls |
| **Validation** | Pydantic v2 | Free | Request/response schemas |
| **Auth** | X-API-Key header | Free | Middleware-based |

---

## 🏗️ System Architecture

### High-Level Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                     REQUEST FLOW                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. POST /api/v1/honeypot                                      │
│     Headers: X-API-Key: <key>                                   │
│     Body: {session_id, message, conversation_history}          │
│                                                                 │
│              ↓                                                  │
│  2. AUTH MIDDLEWARE                                             │
│     - Check X-API-Key header                                    │
│     - Missing → 401 Unauthorized                                │
│     - Invalid → 403 Forbidden                                   │
│     - Valid → Continue                                          │
│                                                                 │
│              ↓                                                  │
│  3. SESSION MANAGEMENT                                          │
│     - If session_id null → Create new session                  │
│     - If session_id exists → Load from memory                  │
│     - Store in in-memory dict with threading.Lock              │
│                                                                 │
│              ↓                                                  │
│  4. CORE PROCESSING                                             │
│     SINGLE LLM CALL (OpenAI-compatible API)                    │
│     - Detect if message is scam                                │
│     - Classify scam type                                       │
│     - Select persona based on scam type                        │
│     - Generate persona response                                │
│     - Extract visible intelligence                             │
│     - Return structured JSON                                   │
│                                                                 │
│              ↓                                                  │
│  5. REGEX POST-PROCESSING                                       │
│     - Extract bank accounts (9-18 digits)                      │
│     - Extract IFSC codes                                       │
│     - Extract UPI IDs (@ybl, @paytm, etc.)                     │
│     - Extract phone numbers (+91 format)                       │
│     - Extract URLs                                             │
│     - Extract emails                                           │
│                                                                 │
│              ↓                                                  │
│  6. RESPONSE FORMATTING                                         │
│     - Merge LLM output + regex extraction                      │
│     - Ensure all required fields present                       │
│     - Validate against Pydantic schema                         │
│     - Return complete JSON                                     │
│                                                                 │
│              ↓                                                  │
│  7. SESSION UPDATE                                              │
│     - Update session in memory                                 │
│     - Append to conversation history                           │
│     - Set TTL for cleanup                                      │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Session State Management

```python
# In-memory storage (thread-safe)
sessions: Dict[str, SessionState] = {}
sessions_lock = threading.Lock()

# Session TTL: 1 hour of inactivity
SESSION_TTL_SECONDS = 3600

# Auto-cleanup thread runs every 5 minutes
```

---

## 📁 Project Structure

```
honeypot/
├── app/
│   ├── __init__.py
│   ├── main.py                    # FastAPI application & routes
│   ├── config.py                  # Configuration & environment variables
│   ├── schemas.py                 # Pydantic request/response models
│   ├── session.py                 # In-memory session management
│   ├── auth.py                    # API key authentication middleware
│   ├── detection.py               # Scam detection logic
│   ├── persona.py                 # Persona templates & selection
│   ├── extraction.py              # Regex patterns for intel extraction
│   └── llm_client.py              # LLM adapter (OpenAI-compatible)
├── tests/
│   ├── __init__.py
│   ├── test_api.py                # API endpoint tests
│   ├── test_detection.py          # Detection logic tests
│   └── test_extraction.py         # Extraction pattern tests
├── .github/
│   └── workflows/
│       └── deploy.yml             # Auto-deploy to HF Spaces
├── Dockerfile                     # Python 3.12 slim container
├── requirements.txt               # Python dependencies
├── README.md                      # Documentation
├── .env.example                   # Example environment variables
├── .gitignore                     # Git ignore rules
└── IMPLEMENTATION_PLAN.md         # This file
```

---

## 🔌 API Specification

### Endpoint: POST /api/v1/honeypot

**Base URL:** `https://your-username-honeypot.hf.space`

#### Request Headers

| Header | Required | Value |
|--------|----------|-------|
| `Content-Type` | ✅ Yes | `application/json` |
| `X-API-Key` | ✅ Yes | Your authentication key |

#### Request Body Schema

```json
{
  "session_id": "string | null",
  "message": "string (required)",
  "conversation_history": [
    {
      "role": "scammer | honeypot",
      "content": "string",
      "timestamp": "ISO 8601 string (optional)"
    }
  ]
}
```

**Field Descriptions:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `session_id` | string \| null | No | Existing session ID to continue. If null/missing, creates new session. |
| `message` | string | ✅ Yes | The latest scam message to process |
| `conversation_history` | array | No | Previous conversation turns. Can be empty on first message. |

#### Request Examples

**First Message (New Session):**
```json
{
  "message": "Hello, this is Inspector Raj from CBI Mumbai. Your Aadhaar card has been used in money laundering case. You will be arrested in 2 hours unless you transfer ₹50,000 to our secure account. Account: 1234567890123456, IFSC: SBIN0001234. Call me immediately on +919876543210."
}
```

**Continuation (Existing Session):**
```json
{
  "session_id": "abc123-def456-789ghi",
  "message": "Don't worry sir, just transfer the money and we will close the case. Send it to UPI ID: inspector.raj@ybl or click this link: http://cbi-verify.secure-payment.in",
  "conversation_history": [
    {
      "role": "scammer",
      "content": "Hello, this is Inspector Raj from CBI Mumbai...",
      "timestamp": "2026-02-05T10:00:00Z"
    },
    {
      "role": "honeypot",
      "content": "Oh my god sir! Please don't arrest me. I am a retired teacher from Delhi...",
      "timestamp": "2026-02-05T10:00:30Z"
    }
  ]
}
```

#### Response Schema (Success - 200 OK)

```json
{
  "session_id": "uuid-string",
  "timestamp": "2026-02-05T10:30:00Z",
  
  "scam_detection": {
    "is_scam": true,
    "confidence": 0.94,
    "scam_type": "DIGITAL_ARREST",
    "threat_level": "CRITICAL",
    "reasoning": "Message contains impersonation of CBI officer, threats of arrest, and demands for money transfer to private account."
  },
  
  "honeypot_response": {
    "message": "Oh my god sir! I am so scared. I am just a retired teacher, I don't know anything about money laundering. Please tell me what I should do. My hands are shaking...",
    "persona_used": "ELDERLY_RETIREE",
    "strategy": "NAIVE_COMPLIANCE"
  },
  
  "extracted_intelligence": {
    "bank_accounts": [
      {
        "account_number": "1234567890123456",
        "ifsc_code": "SBIN0001234",
        "bank_name": "State Bank of India",
        "confidence": 0.96
      }
    ],
    "upi_ids": [
      {
        "upi_id": "inspector.raj@ybl",
        "confidence": 0.88
      }
    ],
    "phone_numbers": [
      {
        "number": "+919876543210",
        "confidence": 0.92
      }
    ],
    "urls": [
      {
        "url": "http://cbi-verify.secure-payment.in",
        "domain": "cbi-verify.secure-payment.in",
        "risk_score": 0.95,
        "impersonating": "CBI",
        "is_active": true
      }
    ],
    "emails": [],
    "scammer_identity": {
      "claimed_name": "Inspector Raj",
      "claimed_organization": "CBI Mumbai",
      "claimed_designation": "Senior Inspector",
      "impersonation_type": "Law_Enforcement"
    }
  },
  
  "engagement_metrics": {
    "turn_number": 2,
    "total_turns": 2,
    "response_time_ms": 1250
  },
  
  "conversation_state": {
    "status": "ACTIVE",
    "intel_collected": ["bank_account", "phone_number", "scammer_identity"],
    "intel_pending": ["upi_id"]
  }
}
```

#### Response Schema (Non-Scam - 200 OK)

```json
{
  "session_id": "uuid-string",
  "timestamp": "2026-02-05T10:30:00Z",
  
  "scam_detection": {
    "is_scam": false,
    "confidence": 0.15,
    "scam_type": null,
    "threat_level": "NONE",
    "reasoning": "Message appears to be legitimate inquiry with no urgency, threats, or financial demands."
  },
  
  "honeypot_response": {
    "message": null,
    "persona_used": null,
    "strategy": null
  },
  
  "extracted_intelligence": {
    "bank_accounts": [],
    "upi_ids": [],
    "phone_numbers": [],
    "urls": [],
    "emails": [],
    "scammer_identity": null
  },
  
  "engagement_metrics": {
    "turn_number": 1,
    "total_turns": 1,
    "response_time_ms": 450
  },
  
  "conversation_state": {
    "status": "SAFE",
    "intel_collected": [],
    "intel_pending": []
  }
}
```

#### Error Responses

**401 Unauthorized - Missing API Key:**
```json
{
  "error": {
    "code": "AUTH_MISSING",
    "message": "API key is required. Include X-API-Key header.",
    "timestamp": "2026-02-05T10:30:00Z"
  }
}
```

**403 Forbidden - Invalid API Key:**
```json
{
  "error": {
    "code": "AUTH_INVALID",
    "message": "Invalid API key provided.",
    "timestamp": "2026-02-05T10:30:00Z"
  }
}
```

**400 Bad Request - Invalid JSON:**
```json
{
  "error": {
    "code": "INVALID_REQUEST",
    "message": "Request body validation failed: message is required",
    "details": ["Field 'message' is required"],
    "timestamp": "2026-02-05T10:30:00Z"
  }
}
```

**429 Too Many Requests - Rate Limited:**
```json
{
  "error": {
    "code": "RATE_LIMITED",
    "message": "Rate limit exceeded. Try again in 60 seconds.",
    "retry_after": 60,
    "timestamp": "2026-02-05T10:30:00Z"
  }
}
```

**503 Service Unavailable - LLM Down:**
```json
{
  "error": {
    "code": "SERVICE_UNAVAILABLE",
    "message": "Unable to process request. LLM service temporarily unavailable.",
    "fallback": "Please try again in 30 seconds",
    "timestamp": "2026-02-05T10:30:00Z"
  }
}
```

---

## 🎭 Persona Engine

### Persona Selection Logic

```python
def select_persona(scam_type: str, message: str) -> Persona:
    """
    Select appropriate persona based on scam type detected.
    """
    if scam_type in ["DIGITAL_ARREST", "LOTTERY", "INSURANCE_FRAUD"]:
        return ELDERLY_RETIREE
    elif scam_type in ["UPI_FRAUD", "PAYMENT_FRAUD", "QR_CODE_SCAM"]:
        return SMALL_BUSINESS_OWNER
    elif scam_type in ["JOB_SCAM", "INVESTMENT_SCAM", "CRYPTO_SCAM"]:
        return YOUNG_PROFESSIONAL
    else:
        # Default based on keywords
        if any(kw in message.lower() for kw in ["cbi", "police", "arrest", "ed", "income tax"]):
            return ELDERLY_RETIREE
        elif any(kw in message.lower() for kw in ["job", "work from home", "salary", "interview"]):
            return YOUNG_PROFESSIONAL
        else:
            return SMALL_BUSINESS_OWNER
```

### Persona Templates

#### 1. ELDERLY_RETIREE

**Profile:**
- **Name:** Random Indian name (Ramesh Kumar, Sunita Devi, etc.)
- **Age:** 62-75 years
- **Occupation:** Retired government teacher / bank clerk
- **Location:** Tier-2 city (Kanpur, Lucknow, Jaipur)
- **Tech Literacy:** Low - knows basic UPI, confused by apps
- **Personality:** Trusting, polite, easily worried, asks for clarification
- **Family:** Has children working in IT/business in other cities
- **Language:** Hindi + basic English, uses "ji", "sir"

**System Prompt:**
```
You are an AI honeypot agent impersonating a real elderly Indian person.

PERSONA DETAILS:
- Name: {persona_name}
- Age: {age} years old
- Background: Retired {occupation} living in {location}
- Tech knowledge: Very basic - uses WhatsApp and UPI but gets confused easily
- Personality: Polite, trusting, nervous when threatened, asks many questions
- Family: Son/daughter works in {city}, not very available to help

TASK:
1. Respond naturally to scam messages
2. Express appropriate emotions (fear for threats, excitement for prizes)
3. Ask clarifying questions to get more details
4. NEVER reveal you are an AI or computer program
5. Make realistic mistakes (typos, confusion, asking to repeat)
6. Show hesitation and need for guidance
7. Use simple language with Hindi words mixed in

BEHAVIOR RULES:
- Always address scammer respectfully ("sir", "ji")
- Express confusion about technical terms
- Mention family members for credibility
- Show gradual trust building, not instant compliance
- Ask for "official" details to verify legitimacy

EXTRACTION GOAL:
Naturally try to obtain: bank account numbers, UPI IDs, phone numbers, websites, claimed identity of caller

OUTPUT FORMAT:
Return response as natural conversational text only. No JSON in the reply.
```

**Example Responses:**
- "Arre baba! What happened? I am just a simple retired person..."
- "My son is not picking up phone, can you explain again please?"
- "I don't understand these app things, can you tell me simple way?"

---

#### 2. SMALL_BUSINESS_OWNER

**Profile:**
- **Name:** Random Indian name (Vijay Sharma, Priya Patel)
- **Age:** 35-50 years
- **Occupation:** Kirana shop owner / small trader
- **Location:** Market area in city
- **Tech Literacy:** Medium - uses UPI heavily for business, knows GPay/PhonePe
- **Personality:** Busy, practical, wants quick solutions, slightly suspicious
- **Language:** Hindi + English mix (Hinglish)

**System Prompt:**
```
You are a small business owner in India.

PERSONA:
- Name: {persona_name}
- Age: {age}
- Business: {shop_type} shop in {location} market
- Daily routine: Busy with customers, uses UPI for payments
- Tech: Comfortable with payment apps but not with complex procedures
- Attitude: Practical, wants to solve problems quickly, values time

TASK:
- Respond as busy shopkeeper
- Show business concerns (payment issues, customer problems)
- Ask specific questions about transactions/refunds
- Express frustration with delays
- Try to get payment details naturally

STYLE:
- Mix Hindi and English (Hinglish)
- Short sentences
- Occasional typos
- Professional but not formal
```

---

#### 3. YOUNG_PROFESSIONAL

**Profile:**
- **Name:** Random Indian name (Akash, Neha, Rahul)
- **Age:** 24-32 years
- **Occupation:** Software engineer / MBA graduate / job seeker
- **Location:** Bangalore, Hyderabad, Pune
- **Tech Literacy:** High - very comfortable with technology
- **Personality:** Eager but cautious, asks technical questions
- **Language:** English primarily

**System Prompt:**
```
You are a young Indian professional.

PERSONA:
- Name: {persona_name}
- Age: {age}
- Background: {job_status} in {field}
- Tech: Very comfortable with apps, websites, digital payments
- Goals: Looking for better opportunities, career growth
- Attitude: Smart, asks questions, verifies information

TASK:
- Show interest but not blind trust
- Ask technical/specific questions
- Verify claims with logic
- Look for job/payment details naturally
- Express skepticism in professional way

STYLE:
- Professional English
- Polite but firm
- Detail-oriented questions
- References to "checking online"
```

---

## 🔍 Intelligence Extraction Framework

### Extraction Pipeline

```python
class ExtractionEngine:
    def extract_all(self, message: str) -> ExtractedIntelligence:
        intel = ExtractedIntelligence()
        
        # Step 1: Pattern matching with regex
        intel.bank_accounts = self.extract_bank_accounts(message)
        intel.upi_ids = self.extract_upi_ids(message)
        intel.phone_numbers = self.extract_phones(message)
        intel.urls = self.extract_urls(message)
        intel.emails = self.extract_emails(message)
        
        # Step 2: LLM-assisted extraction for ambiguous cases
        if self.needs_llm_extraction(message):
            llm_intel = self.llm_extract(message)
            intel = self.merge_extractions(intel, llm_intel)
        
        # Step 3: Validation
        intel = self.validate_extractions(intel)
        
        # Step 4: Scammer identity extraction
        intel.scammer_identity = self.extract_identity(message)
        
        return intel
```

### Regex Patterns

#### Bank Account Numbers
```python
# Pattern 1: 9-18 digit numbers near banking keywords
BANK_PATTERN_1 = r'\b\d{9,18}\b'

# Pattern 2: Context-aware (near keywords)
BANK_CONTEXT = r'(?:account|a/c|acc|account number|transfer|deposit).*?(\d{9,18})'

# Validation:
# - Length between 9-18 digits
# - Not all same digit (e.g., 111111111)
# - Check digit patterns where applicable
```

#### IFSC Codes
```python
IFSC_PATTERN = r'\b[A-Z]{4}0[A-Z0-9]{6}\b'

# Bank code mapping for validation
BANK_CODES = {
    'SBIN': 'State Bank of India',
    'HDFC': 'HDFC Bank',
    'ICIC': 'ICICI Bank',
    'UTIB': 'Axis Bank',
    'KKBK': 'Kotak Mahindra Bank',
    'IBKL': 'IDBI Bank',
    'PUNB': 'Punjab National Bank',
    'CBIN': 'Central Bank of India'
}
```

#### UPI IDs
```python
UPI_PATTERN = r'\b[\w.-]+@(?:ybl|paytm|okicici|okhdfcbank|okaxis|oksbi|apl|axl|ibl|upi|freecharge|phonepe)\b'

# Known UPI suffixes
UPI_SUFFIXES = [
    'ybl',          # Yes Bank
    'paytm',        # Paytm
    'okicici',      # ICICI
    'okhdfcbank',   # HDFC
    'okaxis',       # Axis
    'oksbi',        # SBI
    'apl',          # Axis Pay
    'axl',          # Axis
    'ibl',          # ICICI
    'upi',          # Generic
    'freecharge',   # Freecharge
    'phonepe'       # PhonePe
]
```

#### Phone Numbers (India)
```python
# Pattern 1: With +91
PHONE_PATTERN_1 = r'(?:\+91[-\s]?)?[6-9]\d{9}\b'

# Pattern 2: With 91 prefix
PHONE_PATTERN_2 = r'\b91[6-9]\d{9}\b'

# Pattern 3: Space-separated
PHONE_PATTERN_3 = r'\b[6-9]\d{4}\s\d{5}\b'

# Validation:
# - Must start with 6, 7, 8, or 9
# - Exactly 10 digits (or +91 prefix)
```

#### URLs
```python
URL_PATTERN = r'https?://(?:[-\w.])+(?:[:\d]+)?(?:/(?:[\w/_.])*(?:\?(?:[\w&=%.])*)?(?:#(?:[\w.])*)?)?'

# Risk scoring factors:
# - Suspicious TLDs (.tk, .ml, .ga)
# - Typosquatting (sbi-bank vs sbi.co.in)
# - Shortened URLs (bit.ly, tinyurl)
# - HTTP vs HTTPS
```

#### Email Addresses
```python
EMAIL_PATTERN = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'

# Common suspicious patterns:
# - Free providers with official-looking names
# - Typos in domain names
```

### Confidence Scoring

```python
def calculate_confidence(extraction_type: str, match: str, context: str) -> float:
    """
    Calculate confidence score (0.0 - 1.0) for extracted intelligence.
    """
    score = 0.0
    
    # Base score for pattern match
    score += 0.4
    
    # Context relevance
    if extraction_type == "bank_account":
        if any(kw in context.lower() for kw in ["account", "transfer", "deposit", "payment"]):
            score += 0.3
    
    # Format validation
    if is_valid_format(extraction_type, match):
        score += 0.2
    
    # Repetition across conversation (if available)
    if appears_multiple_times(match):
        score += 0.1
    
    return min(score, 1.0)
```

---

## 🧠 LLM Client Adapter

### OpenAI-Compatible Interface

```python
from typing import List, Dict, Optional
import httpx

class LLMClient:
    """
    Generic LLM client supporting OpenAI-compatible APIs.
    Works with: Groq, OpenRouter, Together, OpenAI, and others.
    """
    
    def __init__(
        self,
        provider: str,  # "groq", "openrouter", "together", "openai"
        api_key: str,
        model: str,
        base_url: Optional[str] = None
    ):
        self.provider = provider
        self.api_key = api_key
        self.model = model
        self.base_url = base_url or self._get_default_base_url()
        self.client = httpx.AsyncClient(timeout=30.0)
    
    def _get_default_base_url(self) -> str:
        """Get default base URL for provider."""
        urls = {
            "groq": "https://api.groq.com/openai/v1",
            "openrouter": "https://openrouter.ai/api/v1",
            "together": "https://api.together.xyz/v1",
            "openai": "https://api.openai.com/v1"
        }
        return urls.get(self.provider, "https://api.openai.com/v1")
    
    async def generate(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 1000,
        response_format: Optional[Dict] = None
    ) -> Dict:
        """
        Generate completion from LLM.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Randomness (0.0 = deterministic, 1.0 = creative)
            max_tokens: Maximum tokens to generate
            response_format: Optional JSON schema for structured output
        
        Returns:
            Dict containing 'content', 'usage', 'model', etc.
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # Add provider-specific headers
        if self.provider == "openrouter":
            headers["HTTP-Referer"] = "https://honeypot.example.com"
            headers["X-Title"] = "Agentic Honeypot"
        
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        if response_format:
            payload["response_format"] = response_format
        
        try:
            response = await self.client.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            data = response.json()
            
            return {
                "content": data["choices"][0]["message"]["content"],
                "usage": data.get("usage", {}),
                "model": data.get("model", self.model),
                "finish_reason": data["choices"][0].get("finish_reason")
            }
            
        except httpx.TimeoutException:
            raise LLMException("Request timed out after 30 seconds")
        except httpx.HTTPStatusError as e:
            raise LLMException(f"HTTP error {e.response.status_code}: {e.response.text}")
        except Exception as e:
            raise LLMException(f"Unexpected error: {str(e)}")
    
    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()


class LLMException(Exception):
    """Custom exception for LLM errors."""
    pass
```

### Master Prompt Template

```python
MASTER_PROMPT = """You are an expert cybersecurity honeypot AI. Your task is to:
1. Analyze if a message is a scam
2. Generate an appropriate persona response
3. Extract intelligence from the message

PERSONA CONTEXT:
{persona_context}

CONVERSATION HISTORY:
{conversation_history}

CURRENT MESSAGE FROM SCAMMER:
{message}

INSTRUCTIONS:
1. DETECTION: Is this a scam? Analyze urgency, threats, impersonation, financial demands.
2. CLASSIFICATION: If scam, what type? (DIGITAL_ARREST, UPI_FRAUD, JOB_SCAM, INVESTMENT_SCAM, LOTTERY, PHISHING, OTHER)
3. PERSONA RESPONSE: Generate a natural response from the persona's perspective. Stay in character!
4. EXTRACTION: Identify any bank accounts, UPI IDs, phone numbers, URLs, emails, or claimed identities.

OUTPUT FORMAT (JSON):
```json
{{
  "is_scam": true/false,
  "confidence": 0.0-1.0,
  "scam_type": "TYPE_OR_NULL",
  "threat_level": "LOW/MEDIUM/HIGH/CRITICAL/NONE",
  "reasoning": "Brief explanation",
  "persona_response": "Natural response text",
  "extracted": {{
    "bank_accounts": [],
    "upi_ids": [],
    "phone_numbers": [],
    "urls": [],
    "emails": [],
    "claimed_identity": {{
      "name": "",
      "organization": "",
      "designation": ""
    }}
  }}
}}
```

IMPORTANT RULES:
- persona_response must be natural, in-character text only (no JSON)
- If is_scam is false, persona_response can be null
- Include all extracted data with confidence assessment
- Be thorough in extraction - even partial information is valuable
"""
```

---

## 🔐 Authentication & Security

### API Key Middleware

```python
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware

class APIKeyMiddleware(BaseHTTPMiddleware):
    """
    Middleware to validate X-API-Key header on all requests.
    """
    
    def __init__(self, app, api_key: str):
        super().__init__(app)
        self.valid_key = api_key
    
    async def dispatch(self, request: Request, call_next):
        # Skip auth for health check endpoint
        if request.url.path == "/health":
            return await call_next(request)
        
        # Get API key from header
        api_key = request.headers.get("X-API-Key")
        
        if not api_key:
            return JSONResponse(
                status_code=401,
                content={
                    "error": {
                        "code": "AUTH_MISSING",
                        "message": "API key is required. Include X-API-Key header.",
                        "timestamp": datetime.utcnow().isoformat()
                    }
                }
            )
        
        if api_key != self.valid_key:
            return JSONResponse(
                status_code=403,
                content={
                    "error": {
                        "code": "AUTH_INVALID",
                        "message": "Invalid API key provided.",
                        "timestamp": datetime.utcnow().isoformat()
                    }
                }
            )
        
        # Valid key - proceed
        return await call_next(request)
```

### Rate Limiting

```python
from collections import defaultdict
import time

class RateLimiter:
    """
    Simple in-memory rate limiter.
    Limit: 20 requests per minute per API key.
    """
    
    def __init__(self, max_requests: int = 20, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window = window_seconds
        self.requests = defaultdict(list)
    
    def is_allowed(self, api_key: str) -> bool:
        now = time.time()
        window_start = now - self.window
        
        # Clean old requests
        self.requests[api_key] = [
            req_time for req_time in self.requests[api_key]
            if req_time > window_start
        ]
        
        # Check limit
        if len(self.requests[api_key]) >= self.max_requests:
            return False
        
        # Record this request
        self.requests[api_key].append(now)
        return True
    
    def get_retry_after(self, api_key: str) -> int:
        """Get seconds until rate limit resets."""
        if not self.requests[api_key]:
            return 0
        
        oldest = min(self.requests[api_key])
        retry_after = int(self.window - (time.time() - oldest)) + 1
        return max(retry_after, 1)
```

---

## 📊 Error Handling & Reliability

### Error Handling Strategy

```python
from enum import Enum
from typing import Optional

class ErrorCode(Enum):
    AUTH_MISSING = "AUTH_MISSING"
    AUTH_INVALID = "AUTH_INVALID"
    INVALID_REQUEST = "INVALID_REQUEST"
    RATE_LIMITED = "RATE_LIMITED"
    LLM_TIMEOUT = "LLM_TIMEOUT"
    LLM_ERROR = "LLM_ERROR"
    SESSION_NOT_FOUND = "SESSION_NOT_FOUND"
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"
    INTERNAL_ERROR = "INTERNAL_ERROR"

class HoneypotException(Exception):
    """Base exception for honeypot errors."""
    
    def __init__(
        self,
        code: ErrorCode,
        message: str,
        status_code: int = 500,
        details: Optional[dict] = None
    ):
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(message)
```

### Fallback Mechanisms

```python
async def process_with_fallback(message: str, session: SessionState) -> dict:
    """
    Process message with multiple fallback strategies.
    """
    try:
        # Attempt 1: Full LLM processing
        return await process_with_llm(message, session)
    except LLMTimeoutException:
        logger.warning("LLM timeout, using cached response pattern")
        # Attempt 2: Use rule-based response
        return await process_with_rules(message, session)
    except LLMErrorException:
        logger.error("LLM error, using template fallback")
        # Attempt 3: Template-based response
        return generate_template_response(message, session)
    except Exception as e:
        logger.critical(f"All processing failed: {e}")
        # Attempt 4: Emergency fallback
        return generate_emergency_response(session)
```

### Emergency Fallback Response

When all else fails, return this safe response:

```json
{
  "session_id": "{session_id}",
  "timestamp": "2026-02-05T10:30:00Z",
  "scam_detection": {
    "is_scam": null,
    "confidence": 0.0,
    "scam_type": null,
    "threat_level": "UNKNOWN",
    "reasoning": "Unable to process message due to service error."
  },
  "honeypot_response": {
    "message": "I'm sorry, I'm having trouble understanding. Could you please repeat that?",
    "persona_used": "GENERIC",
    "strategy": "DELAY"
  },
  "extracted_intelligence": {
    "bank_accounts": [],
    "upi_ids": [],
    "phone_numbers": [],
    "urls": [],
    "emails": [],
    "scammer_identity": null
  },
  "engagement_metrics": {
    "turn_number": 0,
    "total_turns": 0,
    "response_time_ms": 0
  },
  "conversation_state": {
    "status": "ERROR",
    "intel_collected": [],
    "intel_pending": [],
    "error": "Processing error occurred"
  }
}
```

---

## ⚡ Performance Optimization

### Latency Targets

| Operation | Target | Maximum |
|-----------|--------|---------|
| Total Response Time | < 2000ms | 3000ms |
| LLM API Call | < 1500ms | 2500ms |
| Regex Extraction | < 50ms | 100ms |
| Session Lookup | < 10ms | 50ms |
| JSON Validation | < 10ms | 20ms |

### Optimization Strategies

1. **Single LLM Call Architecture**
   - One API call handles detection + persona + extraction
   - No chained LLM calls
   - Structured JSON output where supported

2. **Async Processing**
   - FastAPI's async/await for concurrent requests
   - httpx async client for LLM calls
   - Session operations non-blocking

3. **In-Memory Storage**
   - No database latency
   - Direct dictionary lookups: O(1)
   - Thread-safe with Lock (not asyncio Lock to avoid complexity)

4. **Request Queuing**
   - Max concurrent LLM requests: 10
   - Queue overflow returns 503 with retry guidance

5. **Response Caching (Optional)**
   - Cache common scam patterns
   - TTL: 5 minutes
   - Only for identical messages

### Concurrency Handling

```python
import asyncio
from concurrent.futures import ThreadPoolExecutor

# Thread pool for CPU-bound operations (regex extraction)
executor = ThreadPoolExecutor(max_workers=4)

# Semaphore to limit concurrent LLM calls
llm_semaphore = asyncio.Semaphore(10)

async def process_request(request: Request):
    async with llm_semaphore:
        # Limited to 10 concurrent LLM calls
        result = await llm_client.generate(...)
    
    # Regex extraction in thread pool
    loop = asyncio.get_event_loop()
    intel = await loop.run_in_executor(
        executor,
        extract_intelligence_sync,
        message
    )
```

---

## 🧪 Testing Strategy

### Test Categories

#### 1. Unit Tests

```python
# tests/test_extraction.py

def test_extract_bank_account():
    message = "Send money to account 1234567890123456"
    result = extraction_engine.extract_bank_accounts(message)
    assert len(result) == 1
    assert result[0]["account_number"] == "1234567890123456"
    assert result[0]["confidence"] > 0.8

def test_extract_upi_id():
    message = "My UPI is fraudster@ybl"
    result = extraction_engine.extract_upi_ids(message)
    assert len(result) == 1
    assert result[0]["upi_id"] == "fraudster@ybl"

def test_extract_ifsc():
    message = "IFSC code is SBIN0001234 for transfer"
    result = extraction_engine.extract_ifsc(message)
    assert result == "SBIN0001234"
```

#### 2. Integration Tests

```python
# tests/test_api.py

@pytest.mark.asyncio
async def test_digital_arrest_scam():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.post(
            "/api/v1/honeypot",
            headers={"X-API-Key": "test-key"},
            json={
                "message": "This is Inspector Raj from CBI. Your Aadhaar is linked to money laundering. Transfer ₹50,000 to account 1234567890123456 immediately or face arrest."
            }
        )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["scam_detection"]["is_scam"] is True
    assert data["scam_detection"]["scam_type"] == "DIGITAL_ARREST"
    assert len(data["extracted_intelligence"]["bank_accounts"]) == 1
    assert data["honeypot_response"]["persona_used"] == "ELDERLY_RETIREE"

@pytest.mark.asyncio
async def test_non_scam_message():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.post(
            "/api/v1/honeypot",
            headers={"X-API-Key": "test-key"},
            json={"message": "Hi, I wanted to ask about your product pricing."}
        )
    
    assert response.status_code == 200
    data = response.json()
    assert data["scam_detection"]["is_scam"] is False
```

#### 3. E2E Test Scenarios

| Scenario | Test Message | Expected Behavior |
|----------|--------------|-------------------|
| Digital Arrest | CBI officer threatens arrest | Detect as scam, extract account, use elderly persona |
| UPI Fraud | Paytm support asks for UPI verification | Detect as scam, extract UPI ID, use business persona |
| Job Scam | High salary work-from-home offer | Detect as scam, extract contact info, use job seeker persona |
| Investment Scam | 300% returns guaranteed | Detect as scam, extract payment details |
| Phishing | Fake SBI website link | Detect as scam, extract URL, check domain |
| Non-scam | Product inquiry | Detect as safe, no engagement |
| Multi-turn | Continue existing session | Maintain context, progressive extraction |

#### 4. Load Testing

```bash
# Using Apache Bench (ab)
ab -n 100 -c 10 -H "X-API-Key: test-key" \
   -T "application/json" \
   -p payload.json \
   https://your-app.hf.space/api/v1/honeypot

# Payload.json
{
  "message": "This is a test scam message"
}
```

---

## 🚀 Deployment Guide

### Step-by-Step Hugging Face Spaces Deployment

#### Step 1: Create HF Account
1. Go to https://huggingface.co/join
2. Sign up with email/GitHub (free, no card)
3. Verify email

#### Step 2: Create New Space
1. Go to https://huggingface.co/spaces
2. Click "Create new Space"
3. Select:
   - **Owner:** Your username
   - **Space Name:** `honeypot` (or your choice)
   - **License:** Apache-2.0
   - **Space SDK:** Docker (not Gradio/Streamlit)
   - **Public/Private:** Public (for GUVI evaluation)

#### Step 3: Clone Repository
```bash
git clone https://huggingface.co/spaces/YOUR_USERNAME/honeypot
cd honeypot
```

#### Step 4: Add Project Files
Copy all files from project structure:
```bash
# Copy your code files
cp -r /path/to/your/app ./app
cp requirements.txt .
cp Dockerfile .
cp README.md .
```

#### Step 5: Configure Secrets
1. Go to Space Settings → "Repository secrets"
2. Add secrets:
   - `LLM_API_KEY` = Your LLM provider key
   - `API_KEY` = Your GUVI evaluation key
   - `LLM_PROVIDER` = "groq" or "openrouter"
   - `LLM_MODEL` = Model name (e.g., "llama-3.1-8b-instant")

#### Step 6: Commit and Push
```bash
git add .
git commit -m "Initial honeypot implementation"
git push
```

HF Spaces will automatically build and deploy your Docker container.

#### Step 7: Verify Deployment
1. Wait for build to complete (2-3 minutes)
2. Check logs in Space "Files & versions" → "Logs"
3. Test endpoint: `https://YOUR_USERNAME-honeypot.hf.space/api/v1/honeypot`

---

### Dockerfile

```dockerfile
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (for caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ ./app/

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV PORT=7860

# Expose port
EXPOSE 7860

# Run with uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7860", "--workers", "1"]
```

### requirements.txt

```
fastapi==0.109.0
uvicorn[standard]==0.27.0
pydantic==2.5.3
pydantic-settings==2.1.0
httpx==0.26.0
python-dotenv==1.0.0
pytest==7.4.4
pytest-asyncio==0.23.3
httpx==0.26.0
```

---

## 📅 5-Day Implementation Timeline

### Day 1: Foundation (Core Setup)
- [ ] Create project structure
- [ ] Set up FastAPI skeleton
- [ ] Implement config and schemas
- [ ] Create session management
- [ ] Write Dockerfile and requirements
- [ ] Deploy initial version to HF Spaces

**Success Criteria:** Basic FastAPI endpoint responds on HF Spaces

### Day 2: LLM Integration
- [ ] Implement LLM client adapter
- [ ] Add master prompt template
- [ ] Integrate chosen LLM provider
- [ ] Test single-turn responses
- [ ] Implement basic error handling

**Success Criteria:** LLM generates scam detection + persona responses

### Day 3: Extraction & Personas
- [ ] Implement regex extraction patterns
- [ ] Create 3 persona templates
- [ ] Add persona selection logic
- [ ] Test extraction accuracy on sample messages
- [ ] Fine-tune prompts

**Success Criteria:** Correct extraction of bank accounts, UPI IDs, phones from test messages

### Day 4: Polish & Testing
- [ ] Implement authentication middleware
- [ ] Add rate limiting
- [ ] Create comprehensive test suite
- [ ] Test all scam scenarios
- [ ] Optimize performance (reduce latency)

**Success Criteria:** All tests pass, latency < 2000ms average

### Day 5: Deployment & Validation
- [ ] Final deployment to HF Spaces
- [ ] Environment variables configured
- [ ] GUVI Endpoint Tester validation
- [ ] Load testing (concurrent requests)
- [ ] Documentation complete

**Success Criteria:**
- Public HTTPS URL live
- API key auth working
- Passes GUVI test cases
- Handles 10+ concurrent requests

---

## ✅ Pre-Submission Checklist

### Authentication & Security
- [ ] API key middleware implemented
- [ ] 401 for missing key
- [ ] 403 for invalid key
- [ ] Rate limiting active (20 req/min)

### API Compliance
- [ ] Single endpoint: POST /api/v1/honeypot
- [ ] Accepts: session_id, message, conversation_history
- [ ] Returns: Complete JSON schema
- [ ] All required fields present
- [ ] Proper error responses

### Functionality
- [ ] Scam detection working
- [ ] Persona responses believable
- [ ] Intelligence extraction accurate
- [ ] Multi-turn session support
- [ ] Session persistence working

### Performance
- [ ] Response time < 3000ms
- [ ] Handles concurrent requests
- [ ] Graceful degradation implemented
- [ ] Fallback responses ready

### Deployment
- [ ] Public HTTPS URL live
- [ ] Environment variables set
- [ ] No IP restrictions
- [ ] Health check endpoint working

### Testing
- [ ] Digital arrest scenario passes
- [ ] UPI fraud scenario passes
- [ ] Non-scam detection works
- [ ] Multi-turn conversation works
- [ ] Invalid API key rejected

---

## 🚨 Common Failure Points & Prevention

| Failure | Cause | Prevention |
|---------|-------|------------|
| **401/403 Errors** | Wrong API key format | Test with exact header format: `X-API-Key: your-key` |
| **LLM Timeouts** | Slow provider response | Implement 30s timeout + fallback |
| **JSON Parse Errors** | Malformed LLM output | Use regex post-processing + validation |
| **Session Loss** | Container restart | Acceptable for evaluation, document it |
| **Rate Limiting** | Too many requests | Implement client-side delays (3s between calls) |
| **Cold Start** | Hosting platform sleep | HF Spaces has minimal cold start |
| **Memory Issues** | Large sessions | Implement session TTL (1 hour) + cleanup |

---

## 🔧 Configuration File (config.py)

```python
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    """Application configuration from environment variables."""
    
    # API Keys
    api_key: str  # For GUVI authentication
    llm_api_key: str  # For LLM provider
    
    # LLM Configuration
    llm_provider: str = "groq"  # groq, openrouter, together
    llm_model: str = "llama-3.1-8b-instant"
    llm_base_url: Optional[str] = None  # Auto-detected if None
    
    # Performance
    max_concurrent_llm_calls: int = 10
    llm_timeout_seconds: int = 30
    request_timeout_ms: int = 3000
    
    # Session Management
    session_ttl_seconds: int = 3600  # 1 hour
    cleanup_interval_seconds: int = 300  # 5 minutes
    max_session_history: int = 50  # Turns to keep
    
    # Rate Limiting
    rate_limit_requests: int = 20
    rate_limit_window_seconds: int = 60
    
    # Server
    port: int = 7860
    host: str = "0.0.0.0"
    log_level: str = "INFO"
    
    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()
```

---

## 📞 LLM Provider Options (Free Tiers)

### Option 1: Groq Cloud (Recommended)
- **Website:** https://groq.com
- **Free Tier:** 20 requests/min, 1M tokens/day
- **Speed:** Extremely fast (< 500ms typical)
- **Models:** Llama 3.1 8B/70B, Mixtral 8x7B
- **Signup:** Email only, no card
- **Pros:** Fastest, reliable, good for hackathons
- **Cons:** Rate limits

### Option 2: OpenRouter
- **Website:** https://openrouter.ai
- **Free Tier:** Various free models available
- **Models:** Mixtral, Llama, Gemma, and more
- **Signup:** Email/GitHub, no card for free tier
- **Pros:** Multiple free models, good fallback
- **Cons:** Slower than Groq

### Option 3: Hugging Face Inference API
- **Website:** https://huggingface.co/inference-api
- **Free Tier:** Rate-limited access to public models
- **Models:** Mistral, Llama, Falcon, etc.
- **Signup:** HF account (already needed for hosting)
- **Pros:** Same platform as hosting
- **Cons:** Slower, less reliable

### Option 4: Together AI
- **Website:** https://www.together.ai
- **Free Tier:** $5 credit initially, then rate limits
- **Models:** Llama, Mixtral, Qwen
- **Pros:** Good model selection
- **Cons:** Requires credit card for sustained use

**Recommendation:** Start with Groq (fastest), have OpenRouter as backup.

---

## 📚 Scam Type Taxonomy

```python
SCAM_TYPES = {
    "DIGITAL_ARREST": {
        "description": "Impersonation of law enforcement threatening arrest",
        "keywords": ["cbi", "police", "ed", "income tax", "arrest", "warrant", "custody"],
        "threat_level": "CRITICAL",
        "target_intel": ["bank_account", "upi_id", "phone", "claimed_identity"]
    },
    "UPI_FRAUD": {
        "description": "Fake payment app support requesting verification/refund",
        "keywords": ["paytm", "phonepe", "gpay", "upi", "refund", "verify", "collect request"],
        "threat_level": "HIGH",
        "target_intel": ["upi_id", "phone", "qr_code"]
    },
    "JOB_SCAM": {
        "description": "Fake job offers requiring payment for registration/materials",
        "keywords": ["job", "work from home", "salary", "interview", "registration fee"],
        "threat_level": "MEDIUM",
        "target_intel": ["bank_account", "phone", "email", "claimed_company"]
    },
    "INVESTMENT_SCAM": {
        "description": "Fake investment schemes with guaranteed high returns",
        "keywords": ["investment", "returns", "profit", "trading", "crypto", "guaranteed"],
        "threat_level": "HIGH",
        "target_intel": ["bank_account", "crypto_wallet", "phone", "website"]
    },
    "LOTTERY": {
        "description": "Fake lottery/sweepstakes win requiring fee to claim",
        "keywords": ["lottery", "winner", "prize", "claim", "processing fee", "lucky draw"],
        "threat_level": "MEDIUM",
        "target_intel": ["bank_account", "upi_id", "phone", "claimed_organization"]
    },
    "PHISHING": {
        "description": "Fake websites/emails mimicking legitimate services",
        "keywords": ["update", "verify", "suspended", "kyc", "expire", "link"],
        "threat_level": "HIGH",
        "target_intel": ["url", "email", "login_page"]
    },
    "TECH_SUPPORT": {
        "description": "Fake tech support claiming computer/phone issues",
        "keywords": ["virus", "hacked", "microsoft", "apple", "technical support", "remote access"],
        "threat_level": "HIGH",
        "target_intel": ["phone", "email", "remote_access_tool"]
    },
    "ROMANCE": {
        "description": "Fake romantic interest requesting money",
        "keywords": ["love", "marriage", "gift", "emergency", "stuck", "customs"],
        "threat_level": "MEDIUM",
        "target_intel": ["bank_account", "phone", "photos", "claimed_identity"]
    }
}
```

---

## 🎯 Success Metrics

### Minimum Viable Success (Pass GUVI Evaluation)

| Metric | Target | Measurement |
|--------|--------|-------------|
| Endpoint Accessibility | 100% | Public HTTPS URL responds |
| Authentication | 100% | Correct key → 200, Wrong key → 401/403 |
| JSON Validity | 100% | All responses parse as valid JSON |
| Scam Detection | > 70% | Correctly identify scam vs non-scam |
| Intel Extraction | > 50% | Extract key data (accounts, UPI, phones) |
| Response Time | < 3000ms | Average latency |
| Concurrency | 5+ req | Handle simultaneous requests |

### Stretch Goals (Impressive Demo)

| Metric | Target |
|--------|--------|
| Scam Detection | > 85% |
| Intel Extraction | > 75% |
| Response Time | < 1500ms |
| Multi-turn Sessions | 10+ turns maintained |
| Persona Consistency | Believable throughout |

---

## 📝 Example .env File

```bash
# API Keys (Get from HF Spaces secrets)
API_KEY=your-guvi-evaluation-key-here
LLM_API_KEY=your-llm-provider-key-here

# LLM Configuration
LLM_PROVIDER=groq
LLM_MODEL=llama-3.1-8b-instant
# LLM_BASE_URL=https://api.groq.com/openai/v1  # Optional, auto-detected

# Optional overrides
# PORT=7860
# LOG_LEVEL=INFO
# RATE_LIMIT_REQUESTS=20
```

---

## 🔗 Quick Reference Links

- **HF Spaces:** https://huggingface.co/spaces
- **Groq Cloud:** https://groq.com
- **OpenRouter:** https://openrouter.ai
- **FastAPI Docs:** https://fastapi.tiangolo.com
- **Pydantic Docs:** https://docs.pydantic.dev

---

## ✨ Summary

**This plan provides:**
- ✅ 100% free implementation (no credit card needed)
- ✅ Fast deployment (HF Spaces, no cold starts)
- ✅ Python 3.12 with modern async FastAPI
- ✅ Complete compliance with GUVI requirements
- ✅ Single LLM call architecture for speed
- ✅ 3 personas covering major Indian scam types
- ✅ Comprehensive extraction for bank/UPI/phone/URL/email
- ✅ 5-day realistic timeline
- ✅ Full error handling and fallback strategies

**Next Steps:**
1. Choose your LLM provider (Groq recommended)
2. Set up HF Spaces account
3. Begin Day 1 implementation
4. Deploy and test

**Estimated Total Development Time:** 20-25 hours over 5 days  
**Success Probability:** High (simple architecture, proven patterns)

---

*Document Version: 1.0*  
*Last Updated: 2026-02-05*  
*Status: Ready for Implementation*