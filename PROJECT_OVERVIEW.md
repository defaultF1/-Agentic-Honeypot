# 🛡️ Agentic Honeypot: Project Overview

The **Agentic Honeypot** is an advanced, AI-driven security system designed to identify, engage, and extract intelligence from scammers in real-time. By impersonating vulnerable targets using high-fidelity personas, it traps scammers in realistic conversations to gather actionable threat intelligence.

---

## 🚀 What is Agentic Honeypot?

It's a "scam-trap" that lives between the scammer and a potential victim. When a scammer sends a message, our agent analyzes it using **Google Gemini LLM**, selects a perfect believable persona to respond with, and extracts critical data like bank accounts and crypto wallets—all while keeping the scammer focused on the "bait" and away from real victims.

---

## 🌟 Key Features

### 1. 🧠 State-of-the-Art Intelligence Engine
- **LLM-Powered Analysis:** Uses Gemini Pro to detect scams with 95%+ accuracy.
- **Classification:** Automatically identifies scam types (Digital Arrest, UPI Fraud, Job Scams, etc.).
- **Threat Assessment:** Categorizes scammers from LOW to CRITICAL threat levels.

### 2. 🎭 Advanced Persona Engine
- **8 Dynamic Personas:** From elderly retirees to tech-savvy professionals, each with their own age, occupation, and backstory.
- **Emotional States:** Personas evolve from *Calm* to *Scared*, *Anxious*, or *Suspicious* based on the conversation.
- **Memory System:** Agents remember what they’ve said, ensuring conversation consistency and building trust with the scammer.
- **Multi-language/Hinglish:** Natural mixing of Hindi, English, and regional phrases (Tamil, Punjabi) to match persona backgrounds.

### 3. 🔍 Deep Intelligence Extraction
The system automatically identifies and validates:
- 🏦 **Bank Accounts:** Extracts account numbers and cross-references IFSC codes to identify banks.
- 📱 **UPI IDs:** Detects and validates UPI handles with suspicious pattern detection.
- 📞 **Phone Numbers:** Extracts and validates Indian mobile numbers.
- 🌐 **URLs & Phishing Links:** Analyzes domains for risk scores and typosquatting detection.
- 📧 **Contact Intel:** Gathers emails and scammer identities (claimed names/orgs).
- ₿ **Crypto Wallets:** **[NEW]** Detects Bitcoin (Legacy/SegWit), Ethereum, and Tether (USDT) wallet addresses.

### 4. 🕵️ Anti-Detection Mechanisms
- **Realistic Delays:** Simulates human typing speeds based on persona age and emotional state.
- **Typo Injection:** Adds natural human errors and "self-corrections" to responses.
- **Persona Strategy:** Agents show hesitation, ask follow-up questions, and "act" confused by tech, just like real targets would.

### 5. 🏗️ Production-Grade Architecture
- **FastAPI Core:** High-performance, asynchronous API.
- **Resilience:** Built-in Circuit Breaker and Exponential Backoff for LLM calls.
- **In-Memory Session Management:** TTL-based session cleanup for privacy and performance.
- **Rate Limiting:** Protects the system from being overwhelmed.
- **Real-Time Metrics:** Analytics dashboard tracking requests, detection rates, and latency.

---

## 🛠️ The Tech Stack

- **Backend:** Python 3.11, FastAPI
- **AI/ML:** Google Gemini (Generative AI)
- **Deployment:** Docker, Hugging Face Spaces
- **Utilities:** Pydantic (Settings), HTTPX (Async requests), Regex (Validation)

---

## 🎯 Success Metrics
1. **Low Latency:** < 2s average response time.
2. **High Engagement:** Aims for 10+ turns per session to maximize data extraction.
3. **Intel Density:** Capturing at least one financial identifier per scam session.

---
**Status:** Version 2.0 - Production Ready ✅
**Mission:** Turning the tables on scammers, one message at a time.
