# 🏛️ Enterprise AI Governance Platform (V4)

> **"The smartest, most secure, and carbon-aware gateway for enterprise AI operations."**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Deploy with Render](https://img.shields.io/badge/Deploy%20to-Render-430098?style=flat&logo=render)](https://render.com)
[![Vercel](https://img.shields.io/badge/Deploy%20with-Vercel-000000?style=flat&logo=vercel)](https://vercel.com)

**Enterprise AI Governance Platform** is an ultra-lightweight API gateway designed to solve the three major challenges of corporate AI adoption: **Uncontrolled Costs**, **Security Vulnerabilities**, and **ESG Compliance**.

---

## 🔥 Key Technical Features

### 🛡️ Context-Preserving Anonymization (Bi-directional Mapping)
Unlike traditional "redaction-only" masking, our V4 engine uses a sophisticated **Alias Mapping** system.
- **How it works:** Sensitive data (PII, Korean names, SSN, Account numbers) is identified via advanced Regex and mapped to realistic aliases (e.g., `Alice`, `010-0000-0001`) before being sent to the LLM.
- **Context Integrity:** The LLM receives a logically consistent prompt, maintaining high reasoning quality.
- **Auto-Recovery:** Upon receiving the response, the gateway automatically swaps the aliases back to the original data in the streaming buffer.
- **Coverage:** Optimized for Korean-specific patterns including addresses, bank accounts, and context-aware name detection.

### 🍃 ESG & Carbon Footprint Tracking
We integrate sustainability into AI operations by calculating the environmental impact of every single API call.
- **Metric:** Real-time CO2 emission estimation based on token counts and model energy profiles.
- **Optimization:** Quantifies "Carbon Avoided" through semantic caching and intelligent routing to smaller, energy-efficient models.
- **Visualization:** Dedicated ESG charts in the dashboard for corporate sustainability reporting.

### 💸 Intelligent Multi-Model Routing (Self-Healing)
A proprietary lightweight weighting engine analyzes prompt complexity to optimize cost and performance.
- **Complexity Analysis:** Uses keyword weights, code detection, and sentence structure (RAM < 5MB).
- **Flash-First Strategy:** Routes simple logic/summarization to **Gemini-1.5-Flash**, saving up to 90% in costs.
- **Zero-Downtime Fallback:** If the primary provider (e.g., OpenAI) is down, the gateway immediately switches to an equivalent fallback model (e.g., Gemini-1.5-Pro) within the same stream.

### 🎨 Enterprise-Grade UI/UX
- **Streaming Markdown:** Renders complex code blocks, LaTeX, and tables in real-time as the AI types.
- **Adaptive Theme:** Seamless Dark/Light mode support via `next-themes` and Tailwind CSS v4.
- **BYOK (Bring Your Own Key):** Secure client-side key management. Your keys never leave your browser/server.

---

## 🚀 Deployment Guide

### Backend (FastAPI)
1. Fork this repository.
2. Deploy as a Web Service on **Render** (Free Tier compatible).
3. Set Environment Variables:
   - `OPENAI_API_KEY`: Your OpenAI key.
   - `GEMINI_API_KEY`: Your Google AI key.

### Frontend (Next.js)
1. Deploy to **Vercel**.
2. Set Environment Variable:
   - `NEXT_PUBLIC_API_URL`: Your backend URL.
3. Access your secure AI Command Center.

---

## 🏛️ Business Impact
- **CFO:** Immediate reduction in OPEX via 85%+ API cost optimization.
- **CISO:** Complete data sovereignty and PII leak prevention.
- **ESG Lead:** Automated tracking and reporting of AI-driven carbon emissions.

---

## 📄 License
This project is open-source and licensed under the [MIT License](LICENSE).

---

## 🌟 Support
If this project delivers value to your organization, please **Star** our repository. It motivates us to keep pushing the boundaries of AI Governance!

[GitHub Repository](https://github.com/ttallbamatuyu/LLM-)
