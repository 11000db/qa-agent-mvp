# Day 2 Checklist

## Day 2 목표
오늘의 목표는 QA Agent MVP의 핵심 기준을 만드는 것이다.

구체적으로는 아래 3가지를 완료하는 것을 목표로 한다.

1. 테스트 케이스 구조(JSON schema)를 이해한다.
2. 좋은 테스트 케이스의 기준(QA 리뷰 기준)을 정리한다.
3. 샘플 요구사항을 바탕으로 테스트 케이스 결과물을 직접 확인하고 리뷰한다.

---

## 오늘 완료해야 할 작업

### 1. `schemas/test_case.schema.json` 확인
- 파일을 열어 필수 필드가 무엇인지 읽는다.
- 어떤 정보가 반드시 들어가야 하는지 이해한다.
- 특히 아래 필드를 확인한다.
  - feature_name
  - requirement_summary
  - priority
  - risk_level
  - preconditions
  - test_steps
  - expected_results
  - negative_cases
  - edge_cases
  - traceability

완료 기준:
- 각 필드가 왜 필요한지 대략 설명할 수 있다.

---

### 2. `docs/tc_quality_rubric.md` 읽기
- 좋은 테스트 케이스의 기준을 읽는다.
- 단순히 문장이 자연스러운지보다 QA 관점에서 쓸만한지 판단하는 기준을 이해한다.
- 특히 아래 항목을 집중해서 본다.
  - 요구사항 반영 여부
  - happy path 포함 여부
  - negative case 포함 여부
  - edge case 포함 여부
  - expected result 명확성
  - precondition 명확성
  - 자동화 가능성

완료 기준:
- “좋은 테스트 케이스란 무엇인가?”에 대해 3~5문장으로 설명할 수 있다.

---

### 3. `sample_outputs/login_test_case.json` 확인
- 로그인 기능 예시 테스트 케이스를 읽는다.
- 요구사항과 테스트 케이스가 잘 연결되어 있는지 본다.
- priority와 risk_level이 적절한지 생각해본다.
- negative_cases와 edge_cases가 충분한지 살펴본다.

완료 기준:
- 로그인 기능 테스트 케이스에서 보강이 필요한 부분이 있는지 1개 이상 말할 수 있다.

---

### 4. 로그인 기능 기준으로 수동 리뷰하기
아래 질문에 답해본다.

- 이 테스트 케이스는 로그인 핵심 흐름을 잘 반영했는가?
- happy path가 포함되어 있는가?
- 실패 케이스가 충분한가?
- 입력값 검증이 포함되어 있는가?
- expected result가 구체적인가?
- precondition이 명확한가?
- 자동화 후보로 적절한가?

완료 기준:
- 스스로 “사용 가능 / 보완 필요” 정도는 판단할 수 있다.

---

### 5. 리뷰 메모 남기기
새 파일을 하나 만들어 간단한 메모를 남긴다.

추천 파일명:
- `docs/day2_review_notes.md`

예시로 아래 내용을 적는다.
- 잘된 점
- 부족한 점
- 추가하고 싶은 테스트 포인트
- 자동화 관점에서 좋은 이유
- 실제 서비스였다면 더 보고 싶은 항목

완료 기준:
- 5줄 이상 메모 작성

---

### 6. Git 반영하기
오늘 작업이 끝나면 Git에 반영한다.

사용 명령어:
```bash
git add .
git commit -m "docs: add day2 checklist and review notes"
