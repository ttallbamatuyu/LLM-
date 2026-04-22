import re

# ========================================
# 경량 보안 마스킹 엔진 (순수 Regex 기반)
# Presidio/spaCy 없이 작동하며, 메모리 ~0MB
# ========================================

# 사내 기밀 프로젝트 코드명 (여기에 추가하면 자동 마스킹)
COMPANY_SECRETS = [
    "nebula", "project4", "internal_db", "aurora", "titan",
]

# PII 탐지 정규식 패턴
PATTERNS = [
    (r'\b\d{3}[-.\s]?\d{3,4}[-.\s]?\d{4}\b', '[PHONE]'),           # 전화번호
    (r'\b\d{2,3}-\d{3,4}-\d{4}\b', '[PHONE]'),                      # 한국 전화번호
    (r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL]'),  # 이메일
    (r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b', '[CREDIT_CARD]'),     # 카드번호
    (r'\b\d{6}[-\s]?\d{7}\b', '[SSN]'),                              # 주민번호
]

def sanitize_prompt(prompt: str) -> tuple:
    """
    사용자의 프롬프트에서 개인정보(전화번호, 이메일) 및 사내 기밀을 감지하고 마스킹합니다.
    반환값: (안전하게 변환된 프롬프트, 마스킹 발생 여부 boolean)
    """
    masked = prompt
    is_masked = False
    
    # 1. PII 패턴 마스킹
    for pattern, replacement in PATTERNS:
        new_text = re.sub(pattern, replacement, masked)
        if new_text != masked:
            is_masked = True
            masked = new_text
    
    # 2. 사내 기밀 단어 마스킹 (대소문자 무시)
    for secret in COMPANY_SECRETS:
        pattern = re.compile(re.escape(secret), re.IGNORECASE)
        new_text = pattern.sub('[REDACTED]', masked)
        if new_text != masked:
            is_masked = True
            masked = new_text
    
    return masked, is_masked
