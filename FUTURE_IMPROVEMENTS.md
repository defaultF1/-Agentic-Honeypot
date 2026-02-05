# 🔧 Future Improvements Roadmap

A quick reference for optional enhancements to the Agentic Honeypot.

---

## 1. Crypto Wallet Extraction
**Priority:** Low | **Effort:** ~1 hour

### What It Does
Detects Bitcoin (BTC) and Ethereum (ETH) wallet addresses in scam messages. Scammers increasingly request crypto payments.

### Implementation Sketch
Add these regex patterns to `extraction.py`:
```python
# Bitcoin: 26-35 alphanumeric, starts with 1, 3, or bc1
BTC_PATTERN = r'\b(1|3)[A-HJ-NP-Za-km-z1-9]{25,34}\b|bc1[a-zA-HJ-NP-Z0-9]{39,59}\b'

# Ethereum: 0x followed by 40 hex characters
ETH_PATTERN = r'\b0x[a-fA-F0-9]{40}\b'
```

### New Schema Field
```python
class CryptoWallet(BaseModel):
    address: str
    currency: str  # "BTC" or "ETH"
    confidence: float
```

---

## 2. Prometheus Metrics Export
**Priority:** Low | **Effort:** ~2 hours

### What It Does
Exposes a `/metrics` endpoint in Prometheus format for monitoring tools like Grafana.

### Key Metrics to Track
| Metric | Type | Description |
|--------|------|-------------|
| `honeypot_requests_total` | Counter | Total API requests |
| `honeypot_scams_detected` | Counter | Total scams identified |
| `honeypot_response_latency_seconds` | Histogram | Response time distribution |
| `honeypot_llm_failures_total` | Counter | LLM call failures |
| `honeypot_active_sessions` | Gauge | Current active sessions |

### Implementation Sketch
```python
from prometheus_client import Counter, Histogram, generate_latest

REQUESTS = Counter('honeypot_requests_total', 'Total requests')
LATENCY = Histogram('honeypot_response_latency_seconds', 'Latency')

@app.get("/metrics")
async def prometheus_metrics():
    return Response(generate_latest(), media_type="text/plain")
```

---

## 3. Webhook for Real-Time Intel Alerts
**Priority:** Low | **Effort:** ~3 hours

### What It Does
Sends extracted intelligence (bank accounts, UPI IDs, etc.) to an external service immediately when detected. Useful for feeding a threat intelligence database or alerting security teams.

### Payload Example (sent to webhook URL)
```json
{
  "timestamp": "2026-02-05T23:30:00Z",
  "session_id": "abc-123",
  "scam_type": "DIGITAL_ARREST",
  "threat_level": "CRITICAL",
  "intel": {
    "bank_accounts": ["1234567890123456"],
    "phone_numbers": ["+919876543210"],
    "scammer_name": "Inspector Raj"
  }
}
```

### Implementation Sketch
```python
import httpx

WEBHOOK_URL = os.getenv("INTEL_WEBHOOK_URL")

async def send_intel_alert(intel: dict):
    if WEBHOOK_URL:
        async with httpx.AsyncClient() as client:
            await client.post(WEBHOOK_URL, json=intel, timeout=5)
```
Add this call inside `honeypot_endpoint()` after extraction.

---

## 4. Admin Dashboard UI
**Priority:** Very Low | **Effort:** ~1-2 days

### What It Does
A simple web UI to view:
- Live analytics (requests per minute, scam types)
- Extracted intel history (searchable table)
- Active sessions and their status

### Tech Options
| Option | Pros | Cons |
|--------|------|------|
| Gradio | Fast to build, Python-native | Limited customization |
| Streamlit | Easy, good for dashboards | Separate process |
| React + FastAPI | Full control | More effort |

### Minimum Viable Dashboard
- Single page with 3 cards: Total Requests, Scams Detected, Avg. Response Time
- Table showing last 50 extracted intel items
- Session count gauge

---

## Quick Reference: What to Build First?

If you have extra time, build in this order:

1. **Crypto Wallet Extraction** — Fastest to implement, immediate value
2. **Webhooks** — Enables real-time alerting integrations
3. **Prometheus Metrics** — Useful if you plan to monitor in production
4. **Admin Dashboard** — Only if you have significant time

---

**Document Created:** 2026-02-05
