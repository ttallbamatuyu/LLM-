import redis

try:
    redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
    redis_client.ping()
except Exception:
    redis_client = None

def check_and_deduct_quota(organization_id: str, cost: float, daily_limit: float = 10.0) -> bool:
    """
    고객사(organization_id)의 일일 최대 사용 가능 금액(daily_limit)을 제어합니다.
    (비용 폭탄 방어 아키텍처)
    """
    if not redis_client or cost == 0.0:
        return True
        
    quota_key = f"quota:{organization_id}"
    current_usage = redis_client.get(quota_key)
    
    if current_usage is None:
        current_usage = 0.0
    else:
        current_usage = float(current_usage)
        
    # 할당량 초과 시 False 반환 (HTTP 429)
    if current_usage + cost > daily_limit:
        return False
        
    # 사용량 누적 및 만료 설정(24시간)
    redis_client.incrbyfloat(quota_key, cost)
    redis_client.expire(quota_key, 86400)
    return True
