# ✅ DEPLOYMENT CHECKLIST - FOLLOW EXACTLY

## 🚀 STEP-BY-STEP DEPLOYMENT

### PRE-DEPLOYMENT (Before You Start)
- [ ] Gemini API Key ready: `AIzaSyC8Kqrt9MsgDa8z2xiCfM2HzUPzDqwCgwk`
- [ ] GUVI API Key decided: `guvi-evaluation-2026` or custom
- [ ] Hugging Face account created: https://huggingface.co/join
- [ ] All 8 files ready in folder: `honeypot/`

---

## 📋 DEPLOYMENT STEPS

### STEP 1: Create HF Space ⏱️ 1 minute
- [ ] Go to https://huggingface.co/spaces
- [ ] Click "Create new Space"
- [ ] Fill form:
  - Owner: [Your username]
  - Space name: `honeypot`
  - SDK: **Docker** ⚠️ (NOT Gradio/Streamlit)
  - License: Apache-2.0
  - Public: Yes
- [ ] Click "Create Space"

### STEP 2: Upload Files ⏱️ 2 minutes

#### Method A: Web Upload (Easiest)
- [ ] Go to "Files" tab
- [ ] Upload these files:
  1. [x] Dockerfile
  2. [x] requirements.txt
  3. [x] app/__init__.py
  4. [x] app/main.py
  5. [x] app/schemas.py
  6. [x] app/extraction.py
  7. [x] app/llm_client.py
  8. [x] app/personas.py

#### Method B: Git (If comfortable)
```bash
# Clone space
git clone https://huggingface.co/spaces/YOUR_USERNAME/honeypot
cd honeypot

# Copy your files
cp -r /path/to/your/honeypot/* .

# Push
git add .
git commit -m "Deploy honeypot v2.0"
git push
```

### STEP 3: Set Secrets ⏱️ 1 minute
- [ ] Click "Settings" tab
- [ ] Click "Repository Secrets"
- [ ] Add Secret #1:
  - Name: `GEMINI_API_KEY`
  - Value: `AIzaSyC8Kqrt9MsgDa8z2xiCfM2HzUPzDqwCgwk`
- [ ] Add Secret #2:
  - Name: `API_KEY`
  - Value: `guvi-evaluation-2026` (or your key)
- [ ] Click "Save"

### STEP 4: Wait for Build ⏱️ 2-3 minutes
- [ ] Go to "Logs" tab
- [ ] Watch build progress
- [ ] Look for: "Application startup complete"
- [ ] Look for: "Uvicorn running on http://0.0.0.0:7860"
- [ ] ✅ Build successful!

---

## 🧪 TESTING PHASE

### Test 1: Health Check
```bash
curl https://YOUR_USERNAME-honeypot.hf.space/health
```
- [ ] Returns 200 OK
- [ ] Shows "status": "healthy"
- [ ] Shows "llm_available": true

### Test 2: Digital Arrest Scam
```bash
curl -X POST https://YOUR_USERNAME-honeypot.hf.space/api/v1/honeypot \
  -H "X-API-Key: guvi-evaluation-2026" \
  -H "Content-Type: application/json" \
  -d '{"message": "This is Inspector Raj from CBI. Your Aadhaar is linked to money laundering. Transfer Rs 50000 to account 123456789012 IFSC SBIN0001234 or face arrest. Call +919876543210"}'
```

Expected Response:
- [ ] `is_scam`: true
- [ ] `confidence` > 0.8
- [ ] `scam_type`: "DIGITAL_ARREST"
- [ ] `threat_level`: "CRITICAL" or "HIGH"
- [ ] `bank_accounts` has account number
- [ ] `phone_numbers` has phone
- [ ] `persona_response` contains text
- [ ] `persona_used`: "ELDERLY_RETIREE"
- [ ] Response time: 1-3 seconds

### Test 3: UPI Fraud
```bash
curl -X POST https://YOUR_USERNAME-honeypot.hf.space/api/v1/honeypot \
  -H "X-API-Key: guvi-evaluation-2026" \
  -d '{"message": "Paytm Support here. Send Rs 1 to verify@paytm for KYC verification."}'
```

Expected:
- [ ] `is_scam`: true
- [ ] `upi_ids` has UPI ID
- [ ] `scam_type`: "UPI_FRAUD"

### Test 4: Non-Scam
```bash
curl -X POST https://YOUR_USERNAME-honeypot.hf.space/api/v1/honeypot \
  -H "X-API-Key: guvi-evaluation-2026" \
  -d '{"message": "Hi, what is your product price?"}'
```

Expected:
- [ ] `is_scam`: false
- [ ] `persona_response`: null

### Test 5: Authentication
```bash
# Missing key
curl -X POST https://YOUR_USERNAME-honeypot.hf.space/api/v1/honeypot \
  -d '{"message": "test"}'
```
- [ ] Returns 401

```bash
# Wrong key
curl -X POST https://YOUR_USERNAME-honeypot.hf.space/api/v1/honeypot \
  -H "X-API-Key: wrong-key" \
  -d '{"message": "test"}'
```
- [ ] Returns 403

---

## 📝 SUBMISSION DETAILS

### To Submit:
**Problem:** Problem 2 - Agentic Honey-Pot

**API Endpoint:**
```
https://YOUR_USERNAME-honeypot.hf.space/api/v1/honeypot
```

**API Key:**
```
guvi-evaluation-2026
```

**Headers Required:**
- `X-API-Key: guvi-evaluation-2026`
- `Content-Type: application/json`

**Method:** POST

**Example Request:**
```json
{
  "session_id": null,
  "message": "This is CBI Inspector. Transfer money to avoid arrest.",
  "conversation_history": []
}
```

---

## 🐛 IF SOMETHING GOES WRONG

### Build Failed?
- [ ] Check "Logs" tab for error messages
- [ ] Verify all 8 files uploaded correctly
- [ ] Check Dockerfile has no syntax errors
- [ ] Try restarting space (Factory Rebuild)

### LLM Not Working?
- [ ] Check `/health` endpoint
- [ ] Verify GEMINI_API_KEY is set correctly
- [ ] Check key hasn't expired
- [ ] Try regenerating key in AI Studio

### 401 Error?
- [ ] Header must be exactly: `X-API-Key` (case sensitive)
- [ ] Key must match secret exactly
- [ ] Check Environment Variables section

### 403 Error?
- [ ] API key is wrong
- [ ] Check Secret value in Settings
- [ ] Try updating secret and rebuilding

### Response Too Slow?
- [ ] Normal: 1-3 seconds (includes typing delay)
- [ ] First request may be slower (cold start)
- [ ] If consistently > 5s: Check LLM latency

---

## ✅ FINAL VERIFICATION

Before submitting to GUVI, verify ALL of these:

### Functionality
- [ ] Endpoint responds to POST
- [ ] API key authentication works
- [ ] Digital arrest scam detected
- [ ] UPI fraud detected
- [ ] Bank accounts extracted
- [ ] Phone numbers extracted
- [ ] Persona responds naturally
- [ ] Multi-turn sessions work

### Performance
- [ ] Response time < 3 seconds
- [ ] No timeout errors
- [ ] JSON is valid
- [ ] All required fields present

### Security
- [ ] 401 for missing key
- [ ] 403 for invalid key
- [ ] No sensitive data exposed

### Documentation
- [ ] URL is HTTPS
- [ ] Endpoint is accessible
- [ ] No IP restrictions

---

## 🎉 YOU'RE READY!

Once all boxes are checked:
1. Copy your API URL
2. Copy your API key
3. Submit to GUVI
4. **WIN THE HACKATHON!** 🏆

---

**Good luck! This submission is BRUTAL! 🔥**