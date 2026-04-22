from models import SessionLocal, RequestLog

def log_api_transaction(organization_id: str, prompt_snippet: str, complexity: str, routed_model: str, cost_saved: float):
    """
    라우팅 처리 후 비용 및 통계를 데이터베이스에 기록합니다.
    추후 Client Dashboard에서 이 데이터를 집계하여 보여줍니다.
    """
    db = SessionLocal()
    try:
        new_log = RequestLog(
            organization_id=organization_id,
            prompt_snippet=prompt_snippet[:100],  # 민감도 방지를 위해 앞 100자만 저장
            complexity=complexity,
            routed_model=routed_model,
            cost_saved=cost_saved
        )
        db.add(new_log)
        db.commit()
    except Exception as e:
        print(f"Logging Error: {e}")
    finally:
        db.close()
