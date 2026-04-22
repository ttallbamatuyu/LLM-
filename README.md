<div align="center">

# ⚡ LLM Proxy Gateway

**Cut your LLM API costs by 70%. Protect sensitive data automatically.**

An open-source, enterprise-grade intelligent proxy that sits between your app and LLM providers.
It analyzes every prompt with a local AI, routes to the cheapest model, caches semantically similar queries, and scrubs confidential data — all before a single token leaves your network.

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)](https://python.org)
[![Next.js](https://img.shields.io/badge/Next.js-16-black?logo=next.js)](https://nextjs.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?logo=docker&logoColor=white)](docker-compose.yml)

</div>

---

## 🤔 The Problem

Companies using LLM APIs face **three painful issues**:

1. **💸 Cost Explosion** — Simple "hello" messages get routed to GPT-4, burning $0.03 per query when a $0.0001 model would suffice.
2. **🔓 Data Leaks** — Employees paste internal project names, credentials, and PII directly into ChatGPT prompts.
3. **⏱️ Vendor Lock-in** — When OpenAI goes down, your entire product dies.

**This proxy solves all three. Drop it in front of any LLM API call and it just works.**

---

## ✨ Key Features

### 🧠 AI-Powered Smart Routing
A local **DistilBART** zero-shot classifier analyzes every prompt's intent and complexity in real-time — no API call needed.

| Prompt | Detected Complexity | Routed To | Cost |
|--------|-------------------|-----------|------|
| "Hello, how are you?" | `EASY` | Gemini Flash | $0.0001 |
| "Write a React login form" | `MEDIUM` | GPT-4o | $0.01 |
| "Prove P≠NP with formal logic" | `HARD` | o1-preview | $0.03 |

### ⚡ Semantic Vector Caching
Powered by **Sentence-Transformers**, the gateway embeds every query into a vector space and finds semantically similar past queries.

- ❓ Query 1: *"How do I declare a variable in Python?"*  → API call, cached
- ❓ Query 2: *"Python variable declaration method"* → **Cache Hit!** 0 API calls, 0 cost, instant response

### 🛡️ Automatic Data Scrubbing (PII + Internal Secrets)
Built on **Microsoft Presidio**, the security engine automatically detects and masks:
- Phone numbers, emails, credit cards (PII)
- Internal project codenames (configurable: `NEBULA`, `PROJECT4`, etc.)

```
Input:  "Call 010-1234-5678 about PROJECT4 credentials"
Sent:   "Call [PHONE_NUMBER] about [REDACTED] credentials"
```

### 🌊 Streaming + Graceful Fallback
- Full **SSE (Server-Sent Events)** streaming — characters appear like ChatGPT typing
- If OpenAI is down, the proxy **detects failure on the first byte** and instantly reroutes to Gemini (or vice versa) — the user never sees an error

### 💰 Rate Limiting & Quota Management
Redis-backed per-organization daily spend tracking. When the budget is exhausted, the gateway returns `HTTP 429` immediately — **preventing billing surprises**.

---

## 🏗️ Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                    Your Application                          │
│              (Just change the API URL)                       │
└─────────────────────┬────────────────────────────────────────┘
                      │
                      ▼
┌──────────────────────────────────────────────────────────────┐
│                 ⚡ LLM Proxy Gateway                         │
│                                                              │
│  ┌─────────┐  ┌──────────┐  ┌─────────┐  ┌──────────────┐  │
│  │ Security │→│ AI Router │→│  Cache   │→│   Streaming   │  │
│  │ Scrubber │  │(DistilBART)│ │(Vectors)│  │  + Fallback   │  │
│  └─────────┘  └──────────┘  └─────────┘  └──────┬───────┘  │
│                                                   │          │
│  ┌──────────────┐  ┌───────────────────┐         │          │
│  │ Rate Limiter  │  │  Usage Analytics  │         │          │
│  │  (Redis)      │  │   (SQLite/PG)     │         │          │
│  └──────────────┘  └───────────────────┘         │          │
└──────────────────────────────────────────────────┼──────────┘
                                                   │
                      ┌────────────────────────────┤
                      ▼                            ▼
               ┌────────────┐              ┌────────────┐
               │   OpenAI   │              │   Gemini   │
               │  GPT-4o    │              │  2.0 Flash │
               │  o1-preview│              │  2.0 Pro   │
               └────────────┘              └────────────┘
```

---

## 🆚 How We Compare

| Feature | LiteLLM | Portkey | **LLM Proxy Gateway** |
|---------|---------|---------|----------------------|
| AI-based complexity routing | ❌ | ❌ | ✅ Local DistilBART |
| Semantic vector caching | ❌ | Partial | ✅ Full cosine similarity |
| PII + secret data scrubbing | ❌ | ❌ | ✅ Microsoft Presidio |
| Streaming with auto-fallback | ✅ | ✅ | ✅ First-byte detection |
| Per-org rate limiting | ❌ | ✅ (Paid) | ✅ Free |
| Self-hosted / Open source | ✅ | ❌ | ✅ MIT License |
| BYOK (Bring Your Own Key) | ✅ | ✅ | ✅ |

---

## 🚀 Quick Start

### Option 1: Docker Compose (Recommended)

```bash
git clone https://github.com/ttallbamatuyu/LLM-.git
cd LLM-
docker compose up
```

Open `http://localhost:3000` — done. Backend, frontend, and Redis all spin up automatically.

### Option 2: Manual Setup

**Backend**
```bash
cd backend
python -m venv venv && source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python -m spacy download en_core_web_lg
python app.py
```

**Frontend**
```bash
cd frontend
npm install
npm run dev
```

> **Note:** On first launch, the gateway downloads AI models (~500MB). Subsequent starts are instant.

---

## 🔧 Configuration

| Environment Variable | Description | Default |
|---------------------|-------------|---------|
| `PORT` | Backend server port | `8000` |
| `REDIS_HOST` | Redis server hostname | `localhost` |
| `REDIS_PORT` | Redis server port | `6379` |
| `NEXT_PUBLIC_API_URL` | Backend URL for frontend | `http://localhost:8000` |

---

## 📄 API Usage

Integrate with **one line change** — just swap your OpenAI base URL:

```python
# Before (direct to OpenAI)
client = OpenAI(api_key="sk-...")

# After (through the proxy)
client = OpenAI(
    api_key="sk-...",
    base_url="http://localhost:8000/v1"
)
```

All existing OpenAI SDK code works unchanged. The proxy is fully compatible with the `/v1/chat/completions` endpoint.

---

## 🛣️ Roadmap

- [ ] **Substitution-based masking** — Replace secrets with aliases, restore in response (preserves AI context)
- [ ] **Multi-tenant admin console** — Issue per-org proxy API keys
- [ ] **Audit & security dashboard** — Track blocked data leak attempts
- [ ] **Custom fine-tuned routers** — Upload your data, train domain-specific routing
- [ ] **Multi-modal proxy** — OCR-based image/PDF scrubbing before vision models

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

<div align="center">
  <b>If this project saves you money, consider giving it a ⭐</b>
</div>
