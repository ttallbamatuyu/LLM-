from presidio_analyzer import AnalyzerEngine, PatternRecognizer, Pattern
from presidio_anonymizer import AnonymizerEngine

# 초기화
analyzer = AnalyzerEngine()
anonymizer = AnonymizerEngine()

# 사내 기밀 탐지를 위한 커스텀 사전 및 정규식 규칙 추가
# 예: 사내 프로젝트 코드명 "NEBULA", "PROJECT4" 또는 재무 데이터 패턴 탐지
company_internal_pattern = Pattern(name="internal_code", regex=r"(?i)\b(nebula|project4|internal_db)\b", score=0.9)
company_recognizer = PatternRecognizer(supported_entity="COMPANY_SECRET", patterns=[company_internal_pattern])
analyzer.registry.add_recognizer(company_recognizer)

def sanitize_prompt(prompt: str) -> tuple[str, bool]:
    """
    사용자의 프롬프트에서 개인정보(전화번호, 이메일) 및 지정된 사내 기밀을 감지하고 마스킹(REDACTED) 합니다.
    반환값: (안전하게 변환된 프롬프트, 마스킹 발생 여부 boolean)
    """
    # 1. 개인 정보 및 커스텀 엔티티 감지
    results = analyzer.analyze(text=prompt,
                               entities=["PHONE_NUMBER", "EMAIL_ADDRESS", "COMPANY_SECRET", "CREDIT_CARD"],
                               language='en')
    
    if not results:
        # 마스킹할 내용이 없다면 원본 그대로 반환
        return prompt, False
        
    # 2. 마스킹 (Anonymize)
    anonymized_result = anonymizer.anonymize(text=prompt, analyzer_results=results)
    
    return anonymized_result.text, True
