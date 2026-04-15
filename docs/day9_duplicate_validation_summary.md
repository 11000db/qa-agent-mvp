# Day 9 Duplicate Validation Summary

## 목적
이 문서는 QA Agent MVP의 validator가
negative_cases와 edge_cases 사이의 중복 항목을
정확히 탐지할 수 있는지 검증한 결과를 정리한다.

---

## 검증 대상 파일
- `sample_outputs/invalid_duplicate_test_case.json`

## 사용한 검증 스크립트
- `app/validate_test_case.py`

---

## 테스트 의도
AI가 테스트 케이스를 생성할 때
동일하거나 거의 동일한 문장을
negative_cases와 edge_cases에 중복으로 넣는 경우가 발생할 수 있다.

이러한 중복은 테스트 자산의 품질을 떨어뜨리고,
리뷰 효율과 유지보수성을 낮추므로
자동으로 탐지할 필요가 있다.

---

## 의도적으로 넣은 중복 항목

다음 문장을 일부러
`negative_cases` 와 `edge_cases` 양쪽에 모두 넣었다.

- `잘못된 비밀번호를 입력하면 로그인에 실패하고 오류 메시지가 표시되어야 한다.`

---

## 기대 결과
validator가 아래 항목에서 FAIL을 반환해야 한다.

- `6. negative_cases / edge_cases 중복 여부`

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
- FAIL

### 탐지된 중복 항목
- `잘못된 비밀번호를 입력하면 로그인에 실패하고 오류 메시지가 표시되어야 한다.`

### 최종 결과
- FAIL

---

## 의미
이번 검증을 통해 validator가
단순 형식 검사만 수행하는 것이 아니라,
테스트 케이스 내부의 중복 품질 문제도 자동으로 탐지할 수 있음을 확인했다.

이는 향후 AI가 생성한 테스트 케이스 JSON을 리뷰할 때,
중복된 테스트 포인트를 자동으로 걸러내는 품질 방어막으로 활용될 수 있다.

---

## 현재 validator가 탐지 가능한 항목
- required 필드 누락
- 필수 문자열 공백
- 필수 리스트 공백
- priority 허용값 위반
- risk_level 허용값 위반
- traceability 형식 오류
- negative_cases / edge_cases 중복

---

## 다음 확장 방향
- traceability 중복 ID 검사
- test_steps / expected_results 최소 개수 검사
- 유사 문장(완전 동일 문장 아님) 중복 탐지
- non_functional_checks / test_data 품질 검사
- JSON Schema 기반 정식 validator 연동

---

## 한 줄 정리
validator가 negative_cases와 edge_cases 사이의 중복 항목을 실제로 탐지하고 FAIL 처리함을 확인했다.
