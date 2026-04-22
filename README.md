# 🚀 Enterprise LLM Proxy Gateway V3

> **The ultra-lightweight, secure, and cost-effective entry point for Enterprise AI.**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Deploy with Render](https://img.shields.io/badge/Deploy%20to-Render-430098?style=flat&logo=render)](https://render.com)
[![Vercel](https://img.shields.io/badge/Deploy%20with-Vercel-000000?style=flat&logo=vercel)](https://vercel.com)

**Enterprise LLM Proxy Gateway**는 기업이 AI를 도입할 때 겪는 **보안 위협**과 **비용 폭탄** 문제를 해결하기 위해 설계된 초경량 API 게이트웨이입니다. 단 50MB의 메모리로 구동되며, 실시간 지능형 라우팅과 데이터 마스킹을 제공합니다.

---

## ✨ Key Features (V3)

### 🛡️ Smart Data Masking (PII Protection)
모든 프롬프트는 전송 전 실시간으로 검사됩니다. 이름, 주소, 코드 내 기밀 정보(예: "PROJECT4", "NEBULA")를 자동으로 감지하여 마스킹 처리함으로써 기업의 핵심 데이터 유출을 원천 차단합니다.

### 💸 Intelligent Cost Routing (Flash-First)
자체 개발한 **초경량 가중치 엔진**이 질문의 난이도를 분석합니다. 
- **Simple Question?** -> Gemini-1.5-Flash (비용 90% 절감)
- **Complex Logic?** -> GPT-4o / Gemini-1.5-Pro
- **API Down?** -> 자동 Fallback 시스템으로 무중단 서비스 제공.

### 📊 Real-time Analytics Dashboard
Vercel을 통해 제공되는 미려한 대시보드에서 다음을 실시간으로 확인할 수 있습니다:
- **실시간 비용 절감액:** 프록시 사용 전/후 비용 비교 차트.
- **API 호출 통계:** 어떤 모델이 얼마나 사용되었는지 실시간 트래킹.
- **Playground:** 마스킹과 라우팅이 어떻게 작동하는지 즉시 테스트.

### ⚡ Ultra-Lightweight (Render Free Tier Ready)
PyTorch, Transformers 등 무거운 의존성을 제거하고 순수 로직으로 최적화하여 **RAM 512MB 미만**의 무료 클라우드 환경에서도 완벽하게 동작합니다.

---

## 🛠️ Tech Stack
- **Backend:** FastAPI, Python 3.10+
- **Frontend:** Next.js 14, Tailwind CSS, Recharts
- **Security:** Regex-based PII Scrubber
- **Deployment:** Render (Backend), Vercel (Frontend)

---

## 🚀 Quick Start

### 1. Prerequisites
- OpenAI API Key
- Google Gemini API Key

### 2. Backend Setup (Render)
1. Fork this repository.
2. Connect to Render.com.
3. Deploy as a **Web Service**.
4. Environment Variables:
   - `PORT`: 8000
   - `NEXT_PUBLIC_API_URL`: (Your Vercel URL)

### 3. Frontend Setup (Vercel)
1. Link your forked repository.
2. Environment Variables:
   - `NEXT_PUBLIC_API_URL`: (Your Render Service URL)
3. Build and Deploy.

---

## 📅 Roadmap (V4 & Beyond)
- **Context-Preserving Masking:** 가명 치환 및 원래 데이터 복원 시스템.
- **Virtual API Keys:** 팀별 가상 API 키 발급 및 관리.
- **ESG Reporting:** AI 호출에 따른 탄소 배출량 추적 리포트.
- **Edge sLLM:** 로컬 Gemma 모델 통합으로 0원 라우팅 실현.

---

## 📄 License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🌟 Support
If this project helps you save API costs, please give it a **Star**! it helps a lot.

[GitHub Repository](https://github.com/ttallbamatuyu/LLM-)
