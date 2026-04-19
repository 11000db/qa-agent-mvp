# Day 20 Summary: 최종 데모 완성

## 작업 날짜
2026-04-20

## 목표
전체 파이프라인 end-to-end 실행 및 최종 데모 시나리오 완성

## 작업 내용

### 1. 프롬프트 보완
notes 필드가 단일 문자열로 출력되는 문제 발견
prompts/requirement_to_test_case.md 출력 규칙에 추가:
- notes는 반드시 문자열 배열로 출력
- 단일 문자열 출력 금지

### 2. 최종 데모 실행 결과

**run_pipeline.py 실행:**
```
==================================================
QA Agent MVP - End-to-End Pipeline
==================================================
[Step 1] 테스트 케이스 생성
  - Claude API 호출 중...
  - 저장 완료: sample_outputs\login_test_case.json
[Step 2] 커스텀 검증 (validate_test_case)
  [PASS] 필수 필드 존재
  [PASS] 문자열 필드 공백
  [PASS] 리스트 필드 공백
  [PASS] priority/risk_level 허용값
  [PASS] traceability 형식
  [PASS] negative/edge 교차 중복
  [PASS] test_steps/expected_results 최소 개수
  [PASS] 중복 검사 (traceability/internal/negative/edge)
[Step 3] Schema 검증 (schema_validate_test_case)
  [PASS] JSON Schema 검증
==================================================
최종 결과: PASS ✅
==================================================
```

**Playwright 테스트 실행:**
```
18 passed (1.0m)
```

## 최종 데모 흐름

```
sample_inputs/login_requirement.md (요구사항 입력)
        ↓
python app/run_pipeline.py sample_inputs/login_requirement.md
        ↓
Claude API 호출 → JSON 자동 생성
커스텀 검증 11개 PASS
JSON Schema 검증 PASS
최종 결과: PASS ✅
        ↓
npx playwright test playwright/login.spec.ts
        ↓
18 passed ✅
HTML 리포트 생성 ✅
```

## 전체 작업 이력 (Day 1 ~ Day 20)

| Day | 핵심 작업 |
|-----|----------|
| Day 1~12 | 프롬프트 파이프라인, JSON 설계, validator 구현 |
| Day 13 | negative/edge_cases 내부 중복 검사 추가 |
| Day 14 | JSON Schema 정식 검증 도입 |
| Day 15 | Claude API 연동 테스트 케이스 자동 생성 |
| Day 16 | end-to-end 파이프라인 구현 |
| Day 17 | 검증 결과 markdown 리포트 자동 생성 |
| Day 18 | Playwright 테스트 코드 자동 생성 및 실제 구현 |
| Day 19 | README 포트폴리오용 업데이트 |
| Day 20 | 최종 데모 완성 ✅ |

## 포트폴리오 한 줄 설명

> 요구사항 문서를 입력받아 Claude API로 테스트 케이스를 자동 생성하고, 구조/품질 검증을 거쳐 Playwright 자동화 테스트 코드까지 변환하는 end-to-end QA 파이프라인

## GitHub
https://github.com/11000db/qa-agent-mvp