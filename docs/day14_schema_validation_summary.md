# Day 14 Summary: JSON Schema 정식 검증 도입

## 작업 날짜
2026-04-16

## 목표
jsonschema 라이브러리를 활용한 JSON Schema 정식 검증 도입
기존 커스텀 validator와 schema validator를 함께 운용하는 구조 구성

## 작업 내용

### 1. jsonschema 라이브러리 설치
```
pip install jsonschema
```
- requirements.txt에 jsonschema 추가

### 2. app/schema_validate_test_case.py 생성
- schemas/test_case.schema.json 기준으로 자동 검증
- Draft7Validator 사용
- 커맨드라인 인자로 테스트 케이스 파일 경로 지정 가능
- 스키마 파일 경로도 인자로 지정 가능 (기본값: schemas/test_case.schema.json)

### 3. 검증 흐름
```
테스트 케이스 JSON 파일
        ↓
schema_validate_test_case.py
        ↓
schemas/test_case.schema.json 기준 검증
        ↓
PASS / FAIL 출력
```

## 실행 방법
```powershell
# 기본 실행
python app/schema_validate_test_case.py sample_outputs/login_test_case.json

# 스키마 파일 직접 지정
python app/schema_validate_test_case.py sample_outputs/login_test_case.json schemas/test_case.schema.json
```

## 검증 결과

### PASS 케이스
- 대상: sample_outputs/login_test_case.json
- 결과: Schema 검증 결과: PASS

### FAIL 케이스
- 대상: sample_outputs/invalid_duplicate_negative_edge_cases.json
- 결과: Schema 검증 결과: FAIL
- 발견된 오류:
  - 'feature_name' is a required property
  - 'requirement_summary' is a required property
  - 'priority' is a required property
  - 'risk_level' is a required property
  - 'preconditions' is a required property
  - 'test_steps' is a required property
  - 'expected_results' is a required property
  - 'traceability' is a required property

## 현재 검증 구조
| 파일 | 역할 |
|------|------|
| app/validate_test_case.py | 커스텀 품질 규칙 검증 (중복, 형식, 최소 개수 등) |
| app/schema_validate_test_case.py | JSON Schema 구조 검증 |
| schemas/test_case.schema.json | 스키마 정의 |

## 다음 단계 (Day 15)
- AI 응답 자동 저장 구조 설계
- requirement → prompt → output JSON 저장까지 한 번에 연결