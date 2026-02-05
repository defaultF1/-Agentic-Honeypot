---
title: Agentic Honeypot
emoji: 🍯
colorFrom: yellow
colorTo: orange
sdk: docker
pinned: false
---

# 🛡️ Agentic Honeypot

**The intelligent AI scam trap.**

[![Deployed on Hugging Face](https://img.shields.io/badge/Deployed%20on-Hugging%20Face-blue)](https://huggingface.co/spaces)
[![GUVI Compliant](https://img.shields.io/badge/Status-100%25%20GUVI%20Compliant-green)](LICENSE)

---

## 🚀 About

This is an **Agentic Honeypot** designed to fight back against scammers. It sits between the scammer and the victim, engaging the scammer in realistic conversations to:
1.  **Waste their time** (so they can't target real victims).
2.  **Extract their secrets** (Bank accounts, UPI IDs, Crypto wallets).
3.  **Report them** (to law enforcement/GUVI).

---

## ⚡ Key Features

*   **8 Dynamic Personas**: Impersonates elderly people, tech-savvy youths, etc.
*   **Self-Correction**: Catches AI hallucinations (e.g., "As an AI...") before sending.
*   **Memory Recall**: Remembers conversation details ("You said your name was Inspector Sharma...").
*   **Crypto Extraction**: Detects BTC, ETH, and USDT wallet addresses.

---

## 🛠️ Quick Start

### 1. Requirements
*   Python 3.11+
*   Google Gemini API Key

### 2. Run Locally
```bash
# Clone
git clone https://github.com/defaultF1/-Agentic-Honeypot.git
cd -Agentic-Honeypot

# Install
pip install -r honeypot/requirements.txt

# Run
python -m uvicorn honeypot.app.main:app --host 0.0.0.0 --port 8000
```

### 3. Deploy
See [PROJECT_MASTER_DOCUMENTATION.md](PROJECT_MASTER_DOCUMENTATION.md) for full deployment guide.

---

## 📘 Documentation

Full documentation is available in [PROJECT_MASTER_DOCUMENTATION.md](PROJECT_MASTER_DOCUMENTATION.md).

---

**Built for GUVI GenAI Hackathon 2026** 🏆