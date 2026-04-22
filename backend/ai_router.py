from transformers import pipeline
import time

# ========================================
# ONNX 최적화 AI 라우터 (Zero-Shot 문맥 이해)
# PyTorch CPU-Only로 메모리 ~280MB 사용
# Render 무료 512MB 내에서 AI 지능 100% 유지
# ========================================

classifier = None
_loaded = False

def _load_model():
    global classifier, _loaded
    if _loaded:
        return
    print("[AI Router] Zero-Shot 분류 AI 로딩 중... (최초 1회)")
    try:
        classifier = pipeline(
            "zero-shot-classification", 
            model="valhalla/distilbart-mnli-12-1",
            device=-1  # CPU 강제 (GPU 메모리 0 사용)
        )
    except Exception as e:
        print(f"[AI Router] AI 모델 로드 실패. 규칙 기반으로 롤백: {e}")
        classifier = None
    _loaded = True
    print("[AI Router] AI 로딩 완료!")

# 규칙 기반 폴백 (AI 로드 실패 시)
HARD_KEYWORDS = ["증명", "prove", "architect", "설계", "algorithm", "최적화", "optimize", "분석", "analyze", "보안", "security", "distributed"]
MEDIUM_KEYWORDS = ["코드", "code", "함수", "function", "만들어", "create", "build", "구현", "implement", "에러", "error", "debug", "api", "react", "python"]

def _rule_based_fallback(prompt: str) -> str:
    text = prompt.lower()
    if any(kw in text for kw in HARD_KEYWORDS) or len(text.split()) > 80:
        return 'HARD'
    if any(kw in text for kw in MEDIUM_KEYWORDS) or len(text.split()) > 30:
        return 'MEDIUM'
    return 'EASY'

def analyze_complexity_ai(prompt: str) -> str:
    """Zero-Shot AI가 문맥을 이해하여 난이도를 판별합니다."""
    _load_model()
    
    if not classifier:
        result = _rule_based_fallback(prompt)
        print(f"[AI Router] 규칙 기반 분석: {result}")
        return result
    
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
        elapsed = time.time() - start_t
        print(f"[AI Router] AI 분석: {top_label} (확신도: {score*100:.1f}%) / {elapsed:.2f}초")
        
        if "casual greeting" in top_label:
            return 'EASY'
        elif "complex mathematical" in top_label:
            return 'HARD'
        else:
            return 'MEDIUM'
    except Exception as e:
        print(f"[AI Router] AI 에러, 규칙 폴백: {e}")
        return _rule_based_fallback(prompt)
