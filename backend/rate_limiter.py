# 인메모리 Rate Limiter (Redis 없이도 작동)
from collections import defaultdict
import time

# Redis 연결 시도 (없으면 인메모리 폴백)
try:
    import redis
    redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
    redis_client.ping()
    RATE_BACKEND = "redis"
except Exception:
    redis_client = None
    RATE_BACKEND = "memory"

# 인메모리 사용량 추적
_usage = defaultdict(lambda: {"amount": 0.0, "reset_at": 0})

def check_and_deduct_quota(organization_id: str, cost: float, daily_limit: float = 10.0) -> bool:
    """고객사의 일일 최대 사용 가능 금액을 제어합니다."""
    if cost == 0.0:
        return True
    
    if RATE_BACKEND == "redis" and redis_client:
        quota_key = f"quota:{organization_id}"
        current_usage = redis_client.get(quota_key)
        if current_usage is None:
            current_usage = 0.0
        else:
            current_usage = float(current_usage)
        if current_usage + cost > daily_limit:
            return False
        redis_client.incrbyfloat(quota_key, cost)
        redis_client.expire(quota_key, 86400)
        return True
    else:
        now = time.time()
        entry = _usage[organization_id]
        # 24시간 경과 시 리셋
        if now > entry["reset_at"]:
            entry["amount"] = 0.0
            entry["reset_at"] = now + 86400
        if entry["amount"] + cost > daily_limit:
            return False
        entry["amount"] += cost
        return True
