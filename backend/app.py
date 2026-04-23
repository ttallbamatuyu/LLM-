from fastapi import FastAPI, Request, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from router_engine import route_prompt_stream
from logger_service import log_api_transaction
from models import init_db
from cache_manager import get_semantic_cache, set_semantic_cache
from rate_limiter import check_and_deduct_quota
import json

app = FastAPI(
    title="Enterprise AI Governance Platform",
    description="엔터프라이즈 AI 보안 및 최적화 게이트웨이 V4. 실시간 가명 치환 및 지능형 모델 라우팅 제공.",
    version="4.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def extract_api_keys(request: Request, call_next):
    request.state.openai_key = request.headers.get("X-Openai-Key")
    request.state.gemini_key = request.headers.get("X-Gemini-Key")
    if request.method == "OPTIONS": return await call_next(request)
    return await call_next(request)

@app.post("/v1/chat/completions")
async def proxy_chat_completions(request: Request, background_tasks: BackgroundTasks):
    body = await request.json()
    messages = body.get("messages", [])
    
    if not messages:
        raise HTTPException(status_code=400, detail="No messages provided.")
        
    last_user_message = next((m["content"] for m in reversed(messages) if m["role"] == "user"), "")
    if not last_user_message:
        raise HTTPException(status_code=400, detail="No user message found to route.")

    organization_id = "org_client_b2b"

    # [V3 Feature 1] Rate Limiting Check (과금 폭탄 방지)
    # 호출이 발생하면 즉시 일일 비용 한도를 체크하고 차단합니다.
    if not check_and_deduct_quota(organization_id, 0.01):
        raise HTTPException(status_code=429, detail="[Quota Exceeded] 일일 API 한도를 초과했습니다. 관리자에게 문의하세요.")

    # [V3 Feature 2] Semantic Vector Caching (유사도 캐싱)
    cached_data = get_semantic_cache(last_user_message)
    if cached_data:
        # 캐시에 적중하면 LLM을 안 부르고 한방에 리턴 (스트림 호환 포맷)
        async def cache_stream():
            meta = cached_data.get("meta", {})
            yield f"data: {json.dumps({'content': cached_data['content'], 'meta': meta})}\n\n"
        return StreamingResponse(cache_stream(), media_type="text/event-stream")

    openai_key = request.state.openai_key
    gemini_key = request.state.gemini_key
    if not openai_key and not gemini_key:
        raise HTTPException(status_code=401, detail="Missing API Keys in headers.")

    try:
        # [V3 Feature 3 & 4] 스트리밍 Generator + 초기 연결 우회(Fallback)
        gen, cost_saved, target_model, is_masked = await route_prompt_stream(
            prompt=last_user_message, 
            messages=messages,
            openai_key=openai_key,
            gemini_key=gemini_key
        )
        
        async def event_generator():
            full_response_content = ""
            # 스트림 시작 전, 라우팅 메타데이터를 프론트로 먼저 전달
            meta = {
                "routed_to": target_model,
                "estimated_cost_saved": cost_saved,
                "is_masked": is_masked,
                "cache_hit": False
            }
            yield f"data: {json.dumps({'meta_only': True, 'meta': meta})}\n\n"
            
            # 실시간으로 글자를 쪼개서 SSE 전송
            for chunk_text in gen:
                if chunk_text:
                    full_response_content += chunk_text
                    yield f"data: {json.dumps({'content': chunk_text})}\n\n"

            # 스트리밍 완료 후 사용자 지연 없이 백그라운드로 로깅 및 캐시 적재
            background_tasks.add_task(
                log_api_transaction,
                organization_id,
                last_user_message,
                "EASY" if cost_saved > 0 else "HARD",
                target_model,
                cost_saved
            )
            background_tasks.add_task(
                set_semantic_cache,
                last_user_message,
                full_response_content,
                target_model,
                is_masked
            )

        return StreamingResponse(event_generator(), media_type="text/event-stream")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import os
    init_db()
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("app:app", host="0.0.0.0", port=port, reload=True)
