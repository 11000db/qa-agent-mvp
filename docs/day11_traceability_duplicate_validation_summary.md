# Day 11 Traceability Duplicate Validation Summary

## 목적
이 문서는 QA Agent MVP의 validator가 `traceability` 리스트 내부의 중복 항목을 정확히 탐지할 수 있는지 검증한 결과를 정리한다.

## 검증 대상 파일
- `sample_outputs/invalid_duplicate_traceability_test_case.json`

## 사용한 검증 스크립트
- `app/validate_test_case.py`

## 테스트 의도
기존 validator는 traceability의 형식이 올바른지만 검사했다.  
하지만 형식이 맞더라도 동일한 traceability 문장이 중복으로 들어가면 테스트 케이스의 추적성 품질이 떨어질 수 있다.  
따라서 동일한 traceability 항목이 중복 입력된 경우 FAIL 처리되는지 확인하기 위해 본 검증을 수행했다.

## 의도적으로 넣은 오류

### 1. traceability 중복
- 입력값:
  - `REQ-LOGIN-001: 등록된 사용자는 이메일과 비밀번호로 로그인할 수 있어야 한다.`
  - `REQ-LOGIN-001: 등록된 사용자는 이메일과 비밀번호로 로그인할 수 있어야 한다.`
- 기대 결과:
  - 동일한 traceability 항목 중복으로 FAIL 발생

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
- PASS

### 8. traceability 중복 여부
- FAIL

#### 탐지된 중복 항목
- `REQ-LOGIN-001: 등록된 사용자는 이메일과 비밀번호로 로그인할 수 있어야 한다.`

### 최종 결과
- FAIL

## 의미
validator가 이제 traceability의 형식뿐 아니라 내부 중복까지 확인할 수 있게 되었다.  
이는 테스트 케이스 JSON이 단순히 형식적으로 맞는 수준을 넘어, 추적 가능한 QA 자산으로서 품질을 유지하는 데 도움이 된다.

## 현재 validator가 탐지 가능한 항목
- required 필드 누락
- 필수 문자열 공백
- 필수 리스트 공백
- priority 허용값 위반
- risk_level 허용값 위반
- traceability 형식 오류
- negative_cases / edge_cases 중복
- test_steps / expected_results 최소 개수 부족
- traceability 내부 중복

## 다음 확장 방향
- traceability ID와 설명 간 일관성 검사
- traceability와 requirement_summary 간 의미 연결 검사
- duplicate detection 범위를 preconditions / expected_results까지 확장
- JSON Schema 기반 정식 validator 연동
- AI 응답 저장 직후 자동 검증 및 리포트 생성

## 한 줄 정리
validator가 traceability 내부 중복까지 탐지하며 테스트 케이스의 추적성 품질을 자동으로 검증할 수 있게 되었다.
