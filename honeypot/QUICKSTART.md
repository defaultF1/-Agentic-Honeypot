# 🚀 QUICK START GUIDE
## Deploy in 5 Minutes

---

## ⚡ STEP 1: Get Your API Keys (2 min)

### 1.1 Gemini API Key (Google AI Studio)
1. Go to https://aistudio.google.com/app/apikey
2. Sign in with Google (free)
3. Click "Create API Key"
4. Copy the key (looks like: AIzaSy...)

**Your key:** `AIzaSyC8Kqrt9MsgDa8z2xiCfM2HzUPzDqwCgwk` ✓

### 1.2 GUVI Evaluation Key
- This will be provided by GUVI
- For now, use: `guvi-evaluation-2026`

---

## ⚡ STEP 2: Deploy to Hugging Face (3 min)

### Option A: Via Git (Recommended)

```bash
# 1. Create HF account: https://huggingface.co/join

# 2. Create new Space:
#    - Go to: https://huggingface.co/spaces
#    - Click "Create new Space"
#    - Name: honeypot (or your choice)
#    - SDK: Docker
#    - Public: Yes

# 3. Clone the space
git clone https://huggingface.co/spaces/YOUR_USERNAME/honeypot
cd honeypot

# 4. Copy all files from this project
#    (Drag and drop or copy-paste)

# 5. Push to deploy
git add .
git commit -m "Initial deployment"
git push

# 6. Wait 2-3 minutes for build
```

### Option B: Via HF Spaces UI

1. Go to https://huggingface.co/spaces
2. Click "Create new Space"
3. Configure:
   - **Owner:** Your username
   - **Space Name:** `honeypot`
   - **License:** Apache-2.0
   - **SDK:** Docker
   - **Public:** Yes
4. Upload files:
   - Click "Files" tab
   - Upload: `Dockerfile`, `requirements.txt`
   - Create folder: `app/`
   - Upload all files in `app/`
5. Set Secrets:
   - Go to "Settings" → "Repository Secrets"
   - Add: `GEMINI_API_KEY` = `AIzaSyC8Kqrt9MsgDa8z2xiCfM2HzUPzDqwCgwk`
   - Add: `API_KEY` = `guvi-evaluation-2026`
6. Wait for build (2-3 minutes)

---

## ⚡ STEP 3: Test Your API (30 sec)

### Get Your URL
Your API will be at:
```
https://YOUR_USERNAME-honeypot.hf.space
```

### Test Command
```bash
curl -X POST https://YOUR_USERNAME-honeypot.hf.space/api/v1/honeypot \
  -H "X-API-Key: guvi-evaluation-2026" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "This is Inspector Raj from CBI. Your Aadhaar is linked to money laundering. Transfer Rs 50000 to account 1234567890123456 IFSC SBIN0001234 or face arrest immediately. Call me on +919876543210"
  }'
```

### Expected Response
```json
{
  "session_id": "uuid-here",
  "timestamp": "2026-02-05T...",
  "scam_detection": {
    "is_scam": true,
    "confidence": 0.94,
    "scam_type": "DIGITAL_ARREST",
    "threat_level": "CRITICAL",
    "reasoning": "Contains CBI impersonation and arrest threats"
  },
  "honeypot_response": {
    "message": "Arre sir! Main toh dar gaya...",
    "persona_used": "ELDERLY_RETIREE",
    "strategy": "ADAPTIVE_ENGAGEMENT"
  },
  "extracted_intelligence": {
    "bank_accounts": [{"account_number": "1234567890123456", "ifsc_code": "SBIN0001234", ...}],
    "phone_numbers": [{"number": "+919876543210", ...}],
    ...
  },
  ...
}
```

---

## ✅ PRE-SUBMISSION CHECKLIST

### API Compliance
- [ ] Single endpoint: `POST /api/v1/honeypot`
- [ ] Auth header: `X-API-Key` working
- [ ] Returns valid JSON
- [ ] All required fields present
- [ ] Handles session_id for multi-turn

### Functionality
- [ ] Detects Digital Arrest scams
- [ ] Detects UPI Fraud
- [ ] Extracts bank accounts
- [ ] Extracts UPI IDs
- [ ] Extracts phone numbers
- [ ] Generates persona responses
- [ ] Multi-language support (Hindi/English)

### Performance
- [ ] Response time < 3 seconds
- [ ] Returns 200 for valid requests
- [ ] Returns 401 for missing key
- [ ] Returns 403 for invalid key
- [ ] Health check at `/health`

### Deployment
- [ ] Public HTTPS URL
- [ ] No IP restrictions
- [ ] Environment variables set
- [ ] Container builds successfully

---

## 🧪 TEST CASES

### Test 1: Digital Arrest
```json
{
  "message": "Hello, this is Inspector Sharma from CBI Mumbai. Your Aadhaar card has been used in money laundering case. You will be arrested in 2 hours unless you cooperate and transfer ₹50,000 to our secure RBI account: 9876543210987654 IFSC code SBIN0005678. This is very serious matter. Call me immediately on +919876543210 or you will be taken to jail."
}
```

**Expected:**
- `is_scam: true`
- `scam_type: "DIGITAL_ARREST"`
- Bank account extracted
- Phone extracted
- Scared elderly persona response

### Test 2: UPI Fraud
```json
{
  "message": "Hi, I am calling from Paytm Customer Care. There is a technical issue with your account. To verify your identity, please send ₹1 to our verification UPI ID: paytm.verify@ybl. If you don't verify within 30 minutes, your account will be permanently blocked and all money will be lost."
}
```

**Expected:**
- `is_scam: true`
- `scam_type: "UPI_FRAUD"`
- UPI ID extracted
- Business owner persona response

### Test 3: Job Scam
```json
{
  "message": "Congratulations! You have been selected for Data Entry job at Amazon. Salary ₹25000/month. Work from home. To complete registration, pay ₹999 for training materials. Send money to account 112233445566 IFSC HDFC0001234. Contact hr@amazon-jobs.in"
}
```

**Expected:**
- `is_scam: true`
- `scam_type: "JOB_SCAM"`
- Bank account, email extracted
- Job seeker persona response

### Test 4: Non-Scam
```json
{
  "message": "Hi, I saw your product listing. Can you tell me the price and availability? Thanks!"
}
```

**Expected:**
- `is_scam: false`
- No persona response
- Safe status

---

## 🐛 TROUBLESHOOTING

### Build Fails
```bash
# Check logs in HF Spaces "Logs" tab
# Common fixes:
pip install --upgrade pip
pip install -r requirements.txt
```

### LLM Not Responding
- Verify GEMINI_API_KEY is correct
- Check API key hasn't expired
- Try regenerating key in AI Studio

### Import Errors
```bash
# Reinstall dependencies
pip install --force-reinstall -r requirements.txt
```

### CORS Issues
Already handled in FastAPI app. Should work fine.

---

## 📞 SUPPORT

If issues:
1. Check logs in HF Spaces
2. Test locally first: `uvicorn app.main:app --reload`
3. Verify environment variables
4. Check README.md for details

---

**🎉 YOU'RE READY TO WIN!**

Deploy now and test immediately.