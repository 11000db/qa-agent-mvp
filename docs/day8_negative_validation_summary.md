# Day 8 Negative Validation Summary

## 목적
이 문서는 QA Agent MVP의 validator가
정상 JSON뿐 아니라
의도적으로 잘못 만든 테스트 케이스 JSON에 대해서도
실패를 정확히 탐지할 수 있는지 확인한 결과를 정리한다.

---

## 검증 대상 파일
- `sample_outputs/invalid_login_test_case.json`

## 사용한 검증 스크립트
- `app/validate_test_case.py`

---

## 테스트 의도
정상 케이스만 PASS 하는 것으로는 validator의 품질을 충분히 증명할 수 없다.
따라서 일부 필드를 의도적으로 잘못 작성한 JSON 파일을 만들어
validator가 FAIL을 정확히 탐지하는지 확인했다.

---

## 의도적으로 넣은 오류

### 1. priority 허용값 오류
- 입력값:
  - `"priority": "TOP"`
- 기대 결과:
  - 허용되지 않은 enum 값으로 FAIL 발생

### 2. risk_level 빈 문자열
- 입력값:
  - `"risk_level": ""`
- 기대 결과:
  - 필수 문자열 필드 공백으로 FAIL 발생

### 3. test_steps 빈 리스트
- 입력값:
  - `"test_steps": []`
- 기대 결과:
  - 필수 리스트 필드 공백으로 FAIL 발생

### 4. traceability 형식 오류
- 입력값:
  - `"LOGIN-001 로그인 성공해야 한다"`
- 기대 결과:
  - `REQ-XXX-001: 설명` 형식이 아니므로 FAIL 발생

---

## 실제 검증 결과

### 1. required 필드 존재 여부
- PASS

### 2. 필수 문자열 필드 공백 여부
- FAIL
- 원인:
  - `risk_level`

### 3. 필수 리스트 필드 공백 여부
- FAIL
- 원인:
  - `test_steps`

### 4. priority / risk_level 허용값 여부
- FAIL
- 원인:
  - `priority: TOP`

### 5. traceability 형식 여부
- FAIL
- 원인:
  - `LOGIN-001 로그인 성공해야 한다`

### 최종 결과
- FAIL

---

## 의미
이번 검증을 통해 validator가 단순히 JSON 파일을 읽는 수준이 아니라,
잘못된 값과 형식 오류를 실제로 탐지하는 QA 검사기로 동작함을 확인했다.

이는 향후 AI가 생성한 테스트 케이스 JSON의 품질을 자동 점검할 때
기본적인 방어막 역할을 할 수 있다는 의미가 있다.

---

## 현재 validator가 탐지 가능한 항목
- required 필드 누락
- 필수 문자열 공백
- 필수 리스트 공백
- priority 허용값 위반
- risk_level 허용값 위반
- traceability 형식 오류

---

## 다음 확장 방향
- traceability 중복 검사
- negative_cases와 edge_cases 중복 검사
- test_steps / expected_results 최소 개수 검사
- notes, non_functional_checks, test_data 품질 검사
- JSON Schema 기반 정식 validator 연동

---

## 한 줄 정리
정상 데이터는 PASS하고, 의도적으로 잘못 만든 데이터는 FAIL시키는 검증 흐름이 확인되었다.
