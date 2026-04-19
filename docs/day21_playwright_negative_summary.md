# Day 21 Summary: Playwright Negative Case 실제 구현

## 작업 날짜
2026-04-20

## 목표
login / signup / cart 전체 시나리오 Playwright 실제 구현
Negative Case 구현으로 단순 skeleton에서 실제 동작 검증으로 확장

## 작업 내용

### 1. 테스트 환경
| 기능 | 테스트 사이트 |
|------|-------------|
| 로그인 | https://the-internet.herokuapp.com |
| 회원가입 | https://demoqa.com |
| 장바구니 | https://www.saucedemo.com |

### 2. signup / cart 요구사항 파이프라인 실행
```powershell
python app/run_pipeline.py sample_inputs/signup_requirement.md  # PASS ✅
python app/run_pipeline.py sample_inputs/cart_requirement.md    # PASS ✅
```

### 3. Playwright 코드 자동 생성
```powershell
python app/generate_playwright.py sample_outputs/signup_test_case.json
python app/generate_playwright.py sample_outputs/cart_test_case.json
```

### 4. 실제 구현된 테스트 케이스

**login.spec.ts**
- Happy Path: 정상 로그인 → /secure 이동 확인
- Negative 1: 존재하지 않는 계정 → 에러 메시지 확인
- Negative 2: 올바른 ID + 틀린 PW → 에러 메시지 + 내용 검증
- Negative 3: 빈 username → 에러 메시지 확인
- Negative 4: 빈 password → 에러 메시지 확인
- Negative 5: 완전 빈 필드 → 에러 메시지 확인

**signup.spec.ts**
- Happy Path: 정상 회원가입 → 성공 확인
- Negative 1: 빈 필드 제출 → is-invalid 클래스 확인

**cart.spec.ts**
- Happy Path: 로그인 후 상품 장바구니 추가 → 수량 뱃지 확인
- Negative 1: 비로그인 장바구니 접근 → 로그인 페이지로 리다이렉트
- Negative 2: 상품 추가 후 제거 → 뱃지 사라짐 확인

### 5. 최종 실행 결과
```
51 passed (1.1m)
```

## 테스트 구조
```
playwright/
├── login.spec.ts   → the-internet.herokuapp.com (Happy Path + Negative 1~5 실제 구현)
├── signup.spec.ts  → demoqa.com (Happy Path + Negative 1 실제 구현)
└── cart.spec.ts    → saucedemo.com (Happy Path + Negative 1~2 실제 구현)
```

## 다음 단계 (Day 22~)
- API 테스트 자동화 (pytest + requests)
- 성능 테스트 (Locust)
- CI/CD 연동 (GitHub Actions)