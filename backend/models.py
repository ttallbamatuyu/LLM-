from sqlalchemy import Column, Integer, String, Float, DateTime, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime

Base = declarative_base()

class RequestLog(Base):
    __tablename__ = 'request_logs'
    id = Column(Integer, primary_key=True, autoincrement=True)
    organization_id = Column(String, index=True, default="default_org") # 고객사 식별
    prompt_snippet = Column(String)                                     # 프롬프트 요약
    complexity = Column(String)                                         # 판정된 난이도 (EASY / HARD)
    routed_model = Column(String)                                       # 실제 라우팅 된 모델명
    cost_saved = Column(Float, default=0.0)                             # 절감된 비용 누적용
    created_at = Column(DateTime, default=datetime.utcnow)

# 로컬 SQLite DB로 통계 관리 환경 구성 (상용에서는 Postgres로 대체)
DATABASE_URL = 'sqlite:///c:\\프로젝트4\\backend\\analytics.db'
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)
