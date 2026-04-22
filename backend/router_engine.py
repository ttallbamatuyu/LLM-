import os
import openai
from google import genai
from security_engine import sanitize_prompt
from ai_router import analyze_complexity_ai

async def route_prompt_stream(prompt: str, messages: list, openai_key: str, gemini_key: str):
    # 1. PII 마스킹 (사내 기밀 보호)
    safe_prompt, is_masked = sanitize_prompt(prompt)
    if messages and messages[-1]['role'] == 'user':
        messages[-1]['content'] = safe_prompt
        
    # 2. 초경량 AI 기반 문맥 난이도 파악
    complexity = analyze_complexity_ai(safe_prompt)
    
    combined_prompt = "\n".join([f"{m['role']}: {m['content']}" for m in messages])

    def get_openai_generator(model_name):
        openai.api_key = openai_key
        # 스트리밍 활성화 (yield)
        response = openai.ChatCompletion.create(model=model_name, messages=messages, stream=True)
        # 첫 번째 청크를 받아오면서 API 연결 성공 여부 즉시 판별 (이곳이 핵심 우회 기점)
        first_chunk = next(response)
        def gen():
            # 첫 청크의 글자 반환
            yield first_chunk.choices[0].delta.get("content", "")
            # 나머지 청크 반환
            for chunk in response:
                yield chunk.choices[0].delta.get("content", "")
        return gen()

    # Gemini 모델 우선순위 (최신 → 안정 순서로 자동 시도)
    GEMINI_FLASH_MODELS = ["gemini-2.5-flash-preview-04-17", "gemini-2.0-flash", "gemini-2.0-flash-lite", "gemini-1.5-flash"]
    GEMINI_PRO_MODELS = ["gemini-2.5-pro-preview-05-06", "gemini-2.0-pro", "gemini-1.5-pro"]

    def get_gemini_generator(model_list):
        """모델 리스트를 순서대로 시도하여 첫 번째 성공하는 모델로 스트리밍합니다."""
        client = genai.Client(api_key=gemini_key)
        last_error = None
        for model_name in model_list:
            try:
                response = client.models.generate_content_stream(
                    model=model_name, 
                    contents=combined_prompt
                )
                iterator = iter(response)
                first_chunk = next(iterator)
                def gen(fc=first_chunk, it=iterator):
                    if fc.text:
                        yield fc.text
                    for chunk in it:
                        if chunk.text:
                            yield chunk.text
                print(f"[Gemini] {model_name} 연결 성공!")
                return gen(), model_name
            except Exception as e:
                print(f"[Gemini] {model_name} 실패 → 다음 모델 시도... ({e})")
                last_error = e
                continue
        raise Exception(f"Gemini 모든 모델 실패. 마지막 에러: {last_error}")

    # 3. 우아한 Fallback 라우팅 및 제너레이터 리턴
    if complexity == 'EASY':
        cost_saved = 0.10
        if gemini_key:
            try:
                gen, model_used = get_gemini_generator(GEMINI_FLASH_MODELS)
                return gen, cost_saved, model_used, is_masked
            except Exception as e:
                print(f"[Fallback] Gemini 전체 실패. GPT-4o-mini로 우회합니다.")
                if openai_key:
                    gen = get_openai_generator("gpt-4o-mini")
                    return gen, 0.08, "gpt-4o-mini", is_masked
                else: raise Exception(f"EASY 라우팅 실패 - Gemini: [{e}] (OpenAI 키 없음)")
        elif openai_key:
            gen = get_openai_generator("gpt-4o-mini")
            return gen, 0.08, "gpt-4o-mini", is_masked
            
    elif complexity == 'MEDIUM':
        cost_saved = 0.03
        if openai_key:
            try:
                gen = get_openai_generator("gpt-4o")
                return gen, cost_saved, "gpt-4o", is_masked
            except Exception as e:
                if gemini_key:
                    gen, model_used = get_gemini_generator(GEMINI_PRO_MODELS)
                    return gen, 0.03, model_used, is_masked
                else: raise Exception(f"MEDIUM 라우팅 실패 - OpenAI: [{e}] (Gemini 키 없음)")
        elif gemini_key:
            gen, model_used = get_gemini_generator(GEMINI_PRO_MODELS)
            return gen, 0.03, model_used, is_masked

    else:
        cost_saved = 0.0
        if openai_key:
            try:
                gen = get_openai_generator("o1-preview")
                return gen, cost_saved, "o1-preview", is_masked
            except Exception as e:
                if gemini_key:
                    gen, model_used = get_gemini_generator(GEMINI_PRO_MODELS)
                    return gen, 0.0, model_used, is_masked
                else: raise Exception(f"HARD 라우팅 실패 - OpenAI: [{e}] (Gemini 키 없음)")
        elif gemini_key:
            gen, model_used = get_gemini_generator(GEMINI_PRO_MODELS)
            return gen, 0.0, model_used, is_masked

    raise ValueError("API 키가 누락되었습니다.")
