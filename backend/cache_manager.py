import redis
import json
import numpy as np
from sentence_transformers import SentenceTransformer, util

try:
    redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
    redis_client.ping()
    CACHE_ENABLED = True
except Exception:
    CACHE_ENABLED = False

print("[Cache Manager] 벡터 임베딩 모델 로딩 중... (최초 1회 수십 초 소요)")
try:
    embedder = SentenceTransformer('all-MiniLM-L6-v2')
except Exception as e:
    print(f"[Cache Manager] 모델 로드 실패: {e}")
    embedder = None
print("[Cache Manager] 임베딩 모델 로딩 완료!")

vector_db = [] # 로컬 인메모리 벡터 인덱스

def get_semantic_cache(prompt: str, threshold: float = 0.90):
    """
    의미적 유사도(Cosine Similarity)를 분석하여 90% 이상 일치하는 과거의 응답이 있다면 반환합니다.
    글자가 조금 달라도 의미가 같으면 캐시 히트(Cache Hit)가 발생하여 비용을 100% 절감합니다.
    """
    if not CACHE_ENABLED or not embedder or not vector_db:
        return None
        
    query_embedding = embedder.encode(prompt, convert_to_tensor=True)
    
    best_score = 0
    best_key = None
    
    for item in vector_db:
        score = util.cos_sim(query_embedding, item['embedding'])[0][0].item()
        if score > best_score:
            best_score = score
            best_key = item['key']
            
    if best_score >= threshold and best_key:
        print(f"[Cache Manager] 유사도 {best_score*100:.1f}% 매칭 성공! API 호출 없이 캐시를 반환합니다. (Key: {best_key})")
        cached_data = redis_client.get(best_key)
        if cached_data:
            return json.loads(cached_data)
            
    return None

def set_semantic_cache(prompt: str, response_text: str, routed_model: str, is_masked: bool, ttl_seconds: int = 86400):
    if not CACHE_ENABLED or not embedder:
        return
        
    key = f"semantic_cache:{len(vector_db)}"
    
    response_data = {
        "content": response_text,
        "meta": {
            "routed_to": f"Redis Vector Cache (orig: {routed_model})",
            "estimated_cost_saved": 0.15,
            "is_masked": is_masked,
            "cache_hit": True
        }
    }
    
    redis_client.setex(key, ttl_seconds, json.dumps(response_data))
    
    embedding = embedder.encode(prompt, convert_to_tensor=True)
    vector_db.append({'key': key, 'embedding': embedding})
