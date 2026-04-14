# Pipeline Input / Output Flow

## 목적
이 문서는 QA Agent MVP가 요구사항 파일을 입력받아
프롬프트를 생성하고,
향후 AI를 통해 테스트 케이스 JSON을 만들고,
최종적으로 자동화 가능한 QA 자산으로 확장되는 흐름을 정리한다.

---

## 전체 흐름 요약

1. 요구사항 파일 입력
2. 프롬프트 템플릿 로드
3. 최종 프롬프트 생성
4. AI 호출
5. 테스트 케이스 JSON 생성
6. JSON 스키마 검증
7. 결과 저장
8. 이후 Playwright 코드 변환 가능

---

## 1. 입력(Input)

### 1-1. 요구사항 파일
- 경로 예시:
  - `sample_inputs/login_requirement.md`
  - `sample_inputs/signup_requirement.md`
  - `sample_inputs/cart_requirement.md`

### 1-2. 프롬프트 템플릿
- 경로:
  - `prompts/requirement_to_test_case.md`

### 1-3. JSON 스키마
- 경로:
  - `schemas/test_case.schema.json`

---

## 2. 처리(Process)

### 2-1. 템플릿 + 요구사항 결합
- `app/main.py`가 프롬프트 템플릿 파일을 읽는다.
- 요구사항 파일 내용을 읽는다.
- `{{requirement_text}}` 자리에 실제 요구사항을 삽입한다.
- 최종 프롬프트 텍스트 파일을 생성한다.

### 2-2. AI 호출(향후 추가 예정)
- 생성된 프롬프트를 AI 모델에 전달한다.
- AI는 JSON 형식의 테스트 케이스를 반환해야 한다.

### 2-3. JSON 구조 검증(향후 추가 예정)
- 반환된 JSON이 `test_case.schema.json` 구조를 만족하는지 확인한다.
- 필수 필드 누락 여부를 검사한다.
- expected_results, negative_cases, edge_cases 등이 포함되었는지 확인한다.

---

## 3. 출력(Output)

### 3-1. 프롬프트 출력 파일
- 예시:
  - `sample_outputs/login_prompt.txt`
  - `sample_outputs/signup_prompt.txt`
  - `sample_outputs/cart_prompt.txt`

### 3-2. 테스트 케이스 JSON 출력 파일
- 예시:
  - `sample_outputs/login_test_case.json`
  - `sample_outputs/signup_test_case.json`
  - `sample_outputs/cart_test_case.json`

### 3-3. 향후 확장 출력
- Playwright 테스트 코드
- 실행 결과 로그
- 실패 원인 분류 리포트
- QA 리뷰 문서

---

## 현재까지 구현된 부분
- 요구사항 파일 작성 완료
- 프롬프트 템플릿 작성 완료
- JSON 스키마 초안 작성 완료
- 테스트 케이스 예시(JSON) 작성 완료
- `app/main.py`를 통한 프롬프트 생성 완료

---

## 아직 구현되지 않은 부분
- 실제 AI API 호출
- AI 응답 JSON 자동 저장
- JSON 스키마 자동 검증
- 테스트 케이스 → Playwright 코드 자동 변환
- 실행 결과 자동 수집

---

## 핵심 정리
현재 QA Agent MVP는
**요구사항 → 프롬프트 생성**
단계까지 구현되었고,
다음 단계에서는
**프롬프트 → AI 호출 → 테스트 케이스 JSON 생성**
흐름을 붙이면 된다.
