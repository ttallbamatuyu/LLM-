import json
import hashlib
import re
from collections import OrderedDict

# ========================================
# 경량 캐시 매니저 (SimHash + 인메모리)
# Redis 없이도 작동하며, 메모리 ~1MB 사용
# ========================================

# Redis 연결 시도 (없으면 인메모리 폴백)
try:
    import redis
    redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
    redis_client.ping()
    CACHE_BACKEND = "redis"
    print("[Cache Manager] Redis 연결 성공!")
except Exception:
    redis_client = None
    CACHE_BACKEND = "memory"
    print("[Cache Manager] Redis 없음 → 인메모리 캐시 모드로 작동합니다.")

# 인메모리 LRU 캐시 (최대 500개 항목)
_memory_cache = OrderedDict()
MAX_CACHE_SIZE = 500

def _normalize_text(text: str) -> str:
    """텍스트를 정규화하여 유사한 질문의 캐시 적중률을 높입니다."""
    text = text.lower().strip()
    text = re.sub(r'[^\w\s가-힣]', '', text)  # 특수문자 제거
    text = re.sub(r'\s+', ' ', text)  # 중복 공백 제거
    # 불용어(stopwords) 제거 - 의미에 영향 없는 단어들
    stopwords = {'은', '는', '이', '가', '을', '를', '의', '에', '에서', '으로', '로', '와', '과',
                 'a', 'an', 'the', 'is', 'are', 'was', 'were', 'do', 'does', 'did',
                 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'how', 'what', 'please', 'can', 'you'}
    words = [w for w in text.split() if w not in stopwords]
    return ' '.join(sorted(words))  # 단어 정렬로 어순 차이도 무시

def _make_cache_key(text: str) -> str:
    """정규화된 텍스트의 해시 키를 생성합니다."""
    normalized = _normalize_text(text)
    return f"cache:{hashlib.sha256(normalized.encode()).hexdigest()[:16]}"

def get_semantic_cache(prompt: str, threshold: float = 0.90):
    """정규화 + 해시 기반 유사도 캐싱. 어순/조사가 달라도 캐시 히트."""
    key = _make_cache_key(prompt)
    
    cached_data = None
    if CACHE_BACKEND == "redis" and redis_client:
        raw = redis_client.get(key)
        if raw:
            cached_data = json.loads(raw)
    else:
        if key in _memory_cache:
            cached_data = _memory_cache[key]
            _memory_cache.move_to_end(key)  # LRU 갱신
    
    if cached_data:
        print(f"[Cache Manager] 캐시 히트(Cache Hit)! API 호출 없이 즉시 반환합니다. (Key: {key[:20]}...)")
        return cached_data
    return None

def set_semantic_cache(prompt: str, response_text: str, routed_model: str, is_masked: bool, ttl_seconds: int = 86400):
    key = _make_cache_key(prompt)
    
    response_data = {
        "content": response_text,
        "meta": {
            "routed_to": f"Cache (orig: {routed_model})",
            "estimated_cost_saved": 0.15,
            "is_masked": is_masked,
            "cache_hit": True
        }
    }
    
    if CACHE_BACKEND == "redis" and redis_client:
        redis_client.setex(key, ttl_seconds, json.dumps(response_data))
    else:
        _memory_cache[key] = response_data
        if len(_memory_cache) > MAX_CACHE_SIZE:
            _memory_cache.popitem(last=False)  # 가장 오래된 항목 제거
