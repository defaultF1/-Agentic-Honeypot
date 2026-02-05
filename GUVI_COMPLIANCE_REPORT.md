# 🚨 GUVI API COMPLIANCE REPORT

**Date:** February 6, 2026  
**Status:** ⚠️ **CRITICAL GAPS FOUND**  
**Priority:** MUST FIX BEFORE SUBMISSION

---

## ❌ Critical Issues (MUST FIX)

### 1. Request Schema Mismatch

**GUVI expects:**
```json
{
  "sessionId": "wertyu-dfghj-ertyui",
  "message": {
    "sender": "scammer",
    "text": "Your bank account will be blocked today.",
    "timestamp": 1770005528731
  },
  "conversationHistory": [
    {"sender": "scammer", "text": "...", "timestamp": 123}
  ],
  "metadata": {
    "channel": "SMS",
    "language": "English",
    "locale": "IN"
  }
}
```

**Current implementation:**
```json
{
  "session_id": "...",
  "message": "Your bank account will be blocked today.",
  "conversation_history": [
    {"role": "scammer", "content": "..."}
  ]
}
```

**Differences:**
| Field | GUVI | Current | Action |
|-------|------|---------|--------|
| `sessionId` | camelCase | `session_id` | ⚠️ Fix |
| `message` | Object with `text` | Plain string | ⚠️ Fix |
| `conversationHistory` | camelCase | snake_case | ⚠️ Fix |
| `sender`/`role` | `sender` | `role` | ⚠️ Fix |
| `text`/`content` | `text` | `content` | ⚠️ Fix |
| `metadata` | Required | Missing | ⚠️ Add |

---

### 2. Response Schema Mismatch

**GUVI expects (simple):**
```json
{
  "status": "success",
  "reply": "Why is my account being suspended?"
}
```

**Current implementation (complex):**
```json
{
  "session_id": "...",
  "timestamp": "...",
  "scam_detection": {...},
  "honeypot_response": {...},
  "extracted_intelligence": {...},
  "engagement_metrics": {...},
  "conversation_state": {...}
}
```

**Action:** Must simplify response to match GUVI format.

---

### 3. Missing Mandatory Callback (CRITICAL!)

**GUVI requires** a POST to `https://hackathon.guvi.in/api/updateHoneyPotFinalResult` with:
```json
{
  "sessionId": "abc123-session-id",
  "scamDetected": true,
  "totalMessagesExchanged": 18,
  "extractedIntelligence": {
    "bankAccounts": ["XXXX-XXXX-XXXX"],
    "upiIds": ["scammer@upi"],
    "phishingLinks": ["http://malicious-link.example"],
    "phoneNumbers": ["+91XXXXXXXXXX"],
    "suspiciousKeywords": ["urgent", "verify now"]
  },
  "agentNotes": "Scammer used urgency tactics"
}
```

**Current implementation:** ❌ **NOT IMPLEMENTED**

This is **MANDATORY for scoring**. Without it, the solution **cannot be evaluated**.

---

### 4. Field Naming Convention

| GUVI (camelCase) | Current (snake_case) |
|------------------|---------------------|
| `sessionId` | `session_id` |
| `conversationHistory` | `conversation_history` |
| `scamDetected` | `is_scam` |
| `totalMessagesExchanged` | `turns` |
| `bankAccounts` | `bank_accounts` |
| `upiIds` | `upi_ids` |
| `phishingLinks` | `urls` |

---

## 🔧 Required Fixes

### Fix 1: Update Request Schema (schemas.py)
```python
class GUVIMessage(BaseModel):
    sender: str
    text: str
    timestamp: int

class GUVIMetadata(BaseModel):
    channel: str = "SMS"
    language: str = "English"
    locale: str = "IN"

class GUVIRequest(BaseModel):
    sessionId: str = Field(alias="sessionId")
    message: GUVIMessage
    conversationHistory: List[GUVIMessage] = []
    metadata: Optional[GUVIMetadata] = None
```

### Fix 2: Simplified Response Format
```python
class GUVIResponse(BaseModel):
    status: str  # "success" or "error"
    reply: str   # Agent's response
```

### Fix 3: Add Mandatory Callback Function
```python
async def send_final_result_to_guvi(
    session_id: str,
    scam_detected: bool,
    total_messages: int,
    intel: dict,
    notes: str
):
    payload = {
        "sessionId": session_id,
        "scamDetected": scam_detected,
        "totalMessagesExchanged": total_messages,
        "extractedIntelligence": {
            "bankAccounts": [a.account_number for a in intel.bank_accounts],
            "upiIds": [u.upi_id for u in intel.upi_ids],
            "phishingLinks": [u.url for u in intel.urls],
            "phoneNumbers": [p.number for p in intel.phone_numbers],
            "suspiciousKeywords": []
        },
        "agentNotes": notes
    }
    
    async with httpx.AsyncClient() as client:
        await client.post(
            "https://hackathon.guvi.in/api/updateHoneyPotFinalResult",
            json=payload,
            timeout=5
        )
```

---

## 📊 Compliance Score

| Requirement | Status |
|-------------|--------|
| Request format | ❌ 0% |
| Response format | ❌ 0% |
| Mandatory callback | ❌ 0% |
| API authentication | ✅ 100% |
| Scam detection | ✅ 100% |
| Multi-turn support | ✅ 100% |
| Intelligence extraction | ✅ 100% |

**Overall GUVI Compliance: 40%** ⚠️

---

## ⚡ Immediate Action Required

1. **Update `schemas.py`** - Add GUVI-compatible request/response models
2. **Update `main.py`** - Create new endpoint or adapter for GUVI format
3. **Add callback function** - POST to GUVI evaluation endpoint
4. **Test with GUVI tester** - Verify compliance before submission

**Time Required:** ~30-45 minutes

---

> ⚠️ **Without these fixes, your submission will fail evaluation!**
