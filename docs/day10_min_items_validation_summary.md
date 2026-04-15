# Day 10 Minimum Items Validation Summary

## 목적
이 문서는 QA Agent MVP의 validator가
test_steps와 expected_results의 최소 개수 기준을
정확히 검증할 수 있는지 확인한 결과를 정리한다.

---

## 검증 대상 파일
- `sample_outputs/invalid_min_items_test_case.json`

## 사용한 검증 스크립트
- `app/validate_test_case.py`

---

## 테스트 의도
테스트 케이스가 형식상 필드를 모두 가지고 있더라도,
test_steps나 expected_results가 지나치게 적으면
실무에서 재현 가능성과 검증 가능성이 낮아질 수 있다.

따라서 최소 개수 기준을 두고,
지나치게 빈약한 테스트 케이스를 자동으로 탐지할 수 있는지 확인했다.

---

## 의도적으로 넣은 조건

### 1. test_steps 최소 개수 부족
- 입력값:
  - `test_steps` 1개
- 기대 결과:
  - 최소 2개 기준 미달로 FAIL 발생

### 2. expected_results 최소 개수 부족
- 입력값:
  - `expected_results` 1개
- 기대 결과:
  - 최소 2개 기준 미달로 FAIL 발생

---

## 실제 검증 결과

### 1. required 필드 존재 여부
- PASS

### 2. 필수 문자열 필드 공백 여부
- PASS

### 3. 필수 리스트 필드 공백 여부
- PASS

### 4. priority / risk_level 허용값 여부
- PASS

### 5. traceability 형식 여부
- PASS

### 6. negative_cases / edge_cases 중복 여부
- PASS

### 7. test_steps / expected_results 최소 개수 여부
- FAIL

### 최소 개수 미달 항목
- `test_steps: 1개 (최소 2개 필요)`
- `expected_results: 1개 (최소 2개 필요)`

### 최종 결과
- FAIL

---

## 의미
이번 검증을 통해 validator가
필드 존재 여부와 형식 검사를 넘어서,
테스트 케이스의 최소 구성 품질까지 자동으로 확인할 수 있음을 검증했다.

이는 향후 AI가 생성한 테스트 케이스 JSON이
형식은 맞더라도 지나치게 빈약한 경우를
사전에 걸러내는 품질 방어막 역할을 할 수 있다는 의미가 있다.

---

## 정책 메모
현재 MVP 기준에서는
- `test_steps` 최소 2개
- `expected_results` 최소 2개
를 요구한다.

다만 이 기준은 절대적인 정답이 아니라
초기 품질 기준이며,
향후 기능 특성에 따라 최소 1개 허용 등으로 조정 가능하다.

---

## 다음 확장 방향
- 기능별 최소 개수 기준 분리
- test_steps와 expected_results의 의미적 연결 검사
- overly generic 문장 탐지
- test_data / notes 품질 기준 추가
- JSON Schema 기반 정식 validator 연동

---

## 한 줄 정리
validator가 지나치게 빈약한 테스트 케이스를 최소 개수 기준으로 탐지하고 FAIL 처리함을 확인했다.
