from transformers import pipeline
import time

print("[AI Router] Zero-Shot 분류 AI 로딩 중... (최초 1회 수 초 소요)")
try:
    # 모바일 환경에서도 돌아가는 초경량 DistilBART 모델로 질문의 맥락을 스스로 이해합니다.
    classifier = pipeline("zero-shot-classification", model="valhalla/distilbart-mnli-12-1")
except Exception as e:
    print(f"[AI Router] AI 모델 로드 실패. 기존 규칙 기반 엔진으로 롤백합니다: {e}")
    classifier = None
print("[AI Router] AI 로딩 완료!")

def analyze_complexity_ai(prompt: str) -> str:
    """단순 키워드 매칭을 벗어나, 문맥 자체를 이해하는 AI 라우터 엔진"""
    if not classifier:
        if len(prompt) > 200: return 'HARD'
        return 'EASY'
        
    candidate_labels = [
        "casual greeting, small talk, or simple question", 
        "moderate task like code writing, translation, or summarization", 
        "complex mathematical reasoning, architecture design, or deep analysis"
    ]
    
    try:
        start_t = time.time()
        res = classifier(prompt, candidate_labels)
        top_label = res['labels'][0]
        score = res['scores'][0]
        print(f"[AI Router] 질문 분석 결과: {top_label} (AI 확신도: {score*100:.1f}%) / 분석 속도: {time.time() - start_t:.2f}초")
        
        if "casual greeting" in top_label:
            return 'EASY'
        elif "complex mathematical" in top_label:
            return 'HARD'
        else:
            return 'MEDIUM'
    except Exception as e:
        print(f"[AI Router] 분석 에러: {e}")
        return 'MEDIUM'
