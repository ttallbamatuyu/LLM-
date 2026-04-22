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

    def get_gemini_generator(model_name):
        client = genai.Client(api_key=gemini_key)
        response = client.models.generate_content_stream(
            model=model_name, 
            contents=combined_prompt
        )
        iterator = iter(response)
        first_chunk = next(iterator)
        def gen():
            if first_chunk.text:
                yield first_chunk.text
            for chunk in iterator:
                if chunk.text:
                    yield chunk.text
        return gen()

    # 3. 우아한 Fallback 라우팅 및 제너레이터 리턴
    if complexity == 'EASY':
        cost_saved = 0.10
        if gemini_key:
            try:
                gen = get_gemini_generator("gemini-1.5-flash")
                return gen, cost_saved, "gemini-1.5-flash", is_masked
            except Exception as e:
                print(f"[Fallback] Gemini Flash 연결 실패 ({e}). GPT-4o-mini로 즉각 우회합니다.")
                if openai_key:
                    gen = get_openai_generator("gpt-4o-mini")
                    return gen, 0.08, "gpt-4o-mini", is_masked
                else: raise Exception(f"EASY 라우팅 실패 - Gemini 원본 에러: [{e}] (우회할 OpenAI 키도 없음)")
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
                print(f"[Fallback] GPT-4o 연결 실패 ({e}). Gemini Pro로 즉각 우회합니다.")
                if gemini_key:
                    gen = get_gemini_generator("gemini-1.5-pro")
                    return gen, 0.03, "gemini-1.5-pro", is_masked
                else: raise Exception(f"MEDIUM 라우팅 실패 - OpenAI 원본 에러: [{e}] (우회할 Gemini 키도 없음)")
        elif gemini_key:
            gen = get_gemini_generator("gemini-1.5-pro")
            return gen, 0.03, "gemini-1.5-pro", is_masked

    else:
        cost_saved = 0.0
        if openai_key:
            try:
                gen = get_openai_generator("o1-preview")
                return gen, cost_saved, "o1-preview", is_masked
            except Exception as e:
                print(f"[Fallback] o1-preview 연결 실패 ({e}). Gemini Pro로 즉각 우회합니다.")
                if gemini_key:
                    gen = get_gemini_generator("gemini-1.5-pro")
                    return gen, 0.0, "gemini-1.5-pro", is_masked
                else: raise Exception(f"HARD 라우팅 실패 - OpenAI 원본 에러: [{e}] (우회할 Gemini 키도 없음)")
        elif gemini_key:
            gen = get_gemini_generator("gemini-1.5-pro")
            return gen, 0.0, "gemini-1.5-pro", is_masked

    raise ValueError("API 키가 누락되었습니다.")
