import re
import uuid

# ========================================
# V4 보안 엔진: Context-Preserving Anonymization
# 단순 삭제 대신 가명(Alias)으로 치환하여
# AI 답변 품질을 유지하면서 기밀을 완벽 보호
# ========================================

# 사내 기밀 프로젝트 코드명
COMPANY_SECRETS = [
    "nebula", "project4", "internal_db", "aurora", "titan",
]

# ── 한국형 PII 탐지 정규식 (Phase 2 고도화) ──
PII_PATTERNS = [
    # 주민등록번호 (123456-1234567)
    (r'\b(\d{6})\s*[-]\s*(\d{7})\b', 'SSN'),
    # 전화번호 (010-1234-5678, 02-123-4567 등)
    (r'\b(01[016789])\s*[-.)]\s*(\d{3,4})\s*[-.)]\s*(\d{4})\b', 'PHONE'),
    (r'\b(0\d{1,2})\s*[-.)]\s*(\d{3,4})\s*[-.)]\s*(\d{4})\b', 'PHONE'),
    # 이메일
    (r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', 'EMAIL'),
    # 신용카드 번호
    (r'\b(\d{4})\s*[-\s]?\s*(\d{4})\s*[-\s]?\s*(\d{4})\s*[-\s]?\s*(\d{4})\b', 'CREDIT_CARD'),
    # 계좌번호 (은행명 + 숫자열 패턴)
    (r'\b(\d{3,6})\s*[-]\s*(\d{2,6})\s*[-]\s*(\d{2,6})\b', 'ACCOUNT'),
    # 한국 주소 (xx시/도 xx구/군 xx동/읍/면 패턴)
    (r'([\uAC00-\uD7AF]{1,4}(?:시|도)\s+[\uAC00-\uD7AF]{1,4}(?:구|군|시)\s+[\uAC00-\uD7AF]{1,10}(?:동|읍|면|로|길)\s*[\d-]*)', 'ADDRESS'),
    # 한국 이름 (2~4글자 한글 이름 앞에 "이름은", "성명:", "담당자" 등의 맥락이 있을 때)
    (r'(?:이름은?\s*:?\s*|성명\s*:?\s*|담당자\s*:?\s*|고객\s*:?\s*)([\uAC00-\uD7AF]{2,4})', 'PERSON'),
]

# ── 가명(Alias) 생성기 ──
ALIAS_POOL = {
    'PERSON':      ['홍길동', '김영희', '이철수', '박민수', '최지은', '정수아', '강태현', '윤서연'],
    'PHONE':       ['010-0000-0001', '010-0000-0002', '010-0000-0003', '010-0000-0004'],
    'EMAIL':       ['user_a@example.com', 'user_b@example.com', 'user_c@example.com'],
    'SSN':         ['000000-0000001', '000000-0000002', '000000-0000003'],
    'CREDIT_CARD': ['0000-0000-0000-0001', '0000-0000-0000-0002'],
    'ACCOUNT':     ['000-000-000001', '000-000-000002'],
    'ADDRESS':     ['서울시 강남구 테헤란로 1', '경기도 성남시 분당구 판교로 2'],
    'SECRET':      ['PROJECT_ALPHA', 'PROJECT_BETA', 'PROJECT_GAMMA', 'PROJECT_DELTA'],
}


class AliasMapper:
    """
    가명 치환 매핑 테이블.
    같은 원본 값은 항상 같은 가명으로 치환되며,
    답변 수신 후 가명 → 원본으로 자동 복원할 수 있습니다.
    """
    def __init__(self):
        self.forward_map = {}   # 원본 → 가명
        self.reverse_map = {}   # 가명 → 원본
        self.counters = {}      # 카테고리별 사용된 가명 인덱스

    def get_alias(self, original: str, category: str) -> str:
        """원본 값에 대한 가명을 반환합니다. 이미 매핑되어 있으면 재사용."""
        if original in self.forward_map:
            return self.forward_map[original]

        pool = ALIAS_POOL.get(category, [])
        idx = self.counters.get(category, 0)

        if idx < len(pool):
            alias = pool[idx]
        else:
            # 풀 소진 시 고유 식별자로 대체
            alias = f"[{category}_{idx + 1}]"

        self.counters[category] = idx + 1
        self.forward_map[original] = alias
        self.reverse_map[alias] = original
        return alias

    def restore(self, text: str) -> str:
        """가명이 포함된 텍스트를 원본 데이터로 복원합니다."""
        restored = text
        # 긴 가명부터 먼저 치환해야 부분 매칭 충돌 방지
        for alias, original in sorted(self.reverse_map.items(), key=lambda x: -len(x[0])):
            restored = restored.replace(alias, original)
        return restored

    def get_mapping_summary(self) -> dict:
        """현재 매핑 테이블 요약 (디버그/대시보드용)"""
        return {
            "total_masked": len(self.forward_map),
            "categories": dict(self.counters),
            "mappings": {k: v for k, v in self.forward_map.items()}
        }


def sanitize_prompt(prompt: str) -> tuple:
    """
    V4 가명 치환형 보안 엔진.
    원본 데이터를 가명(Alias)으로 치환하여 AI 답변 품질을 유지하면서 기밀을 보호합니다.

    반환값: (안전한 프롬프트, 마스킹 발생 여부, AliasMapper 인스턴스)
    """
    mapper = AliasMapper()
    masked = prompt
    is_masked = False

    # 1. PII 패턴 가명 치환
    for pattern, category in PII_PATTERNS:
        matches = list(re.finditer(pattern, masked))
        for match in reversed(matches):  # 뒤에서부터 치환해야 인덱스 안 꼬임
            original = match.group(0)
            alias = mapper.get_alias(original, category)
            masked = masked[:match.start()] + alias + masked[match.end():]
            is_masked = True

    # 2. 사내 기밀 단어 가명 치환
    for secret in COMPANY_SECRETS:
        regex = re.compile(re.escape(secret), re.IGNORECASE)
        matches = list(regex.finditer(masked))
        for match in reversed(matches):
            original = match.group(0)
            alias = mapper.get_alias(original.lower(), 'SECRET')
            masked = masked[:match.start()] + alias + masked[match.end():]
            is_masked = True

    if is_masked:
        summary = mapper.get_mapping_summary()
        print(f"[Security V4] 가명 치환 완료: {summary['total_masked']}건 | 카테고리: {summary['categories']}")

    return masked, is_masked, mapper
