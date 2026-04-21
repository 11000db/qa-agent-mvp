# Day 22 Summary: API 테스트 자동화 구현

## 작업 날짜
2026-04-21

## 목표
pytest + requests를 활용한 API 테스트 자동화 구현
포트폴리오 흐름 (요구사항 → TC 생성 → UI 테스트) 에 API 레벨 검증 추가

## 테스트 대상
- **사이트:** https://dummyjson.com
- **API:** POST /auth/login (로그인 API)
- **선택 이유:** 포트폴리오 주요 기능인 로그인과 동일한 도메인, UI 테스트와 연결되는 흐름

## 기술 스택
| 구분 | 기술 |
|------|------|
| 테스트 프레임워크 | pytest |
| HTTP 클라이언트 | requests |
| 리포트 생성 | pytest-html |

## 구현된 테스트 케이스 (6개)

| 테스트명 | 분류 | 검증 내용 |
|---------|------|---------|
| test_login_success | Happy Path | 정상 로그인 → 200, accessToken 존재 확인 |
| test_login_wrong_password | Negative | 잘못된 비밀번호 → 400 확인 |
| test_login_missing_username | Negative | username 누락 → 400 확인 |
| test_login_missing_password | Negative | password 누락 → 400 확인 |
| test_login_empty_body | Negative | 빈 요청 → 400 확인 |
| test_login_response_structure | 구조 검증 | 응답 필드 (accessToken, refreshToken, id, email) 존재 확인 |

## 실행 결과
```
6 passed in 3.12s
```

## 실행 명령어
```powershell
# 테스트 실행
pytest tests/test_api_login.py -v

# HTML 리포트 생성
pytest tests/test_api_login.py -v --html=sample_reports/api_test_report.html
```

## 포트폴리오 전체 흐름 (현재)
```
요구사항 문서 (sample_inputs/*.md)
        ↓
Claude API → 테스트케이스 JSON 자동 생성
        ↓
커스텀 검증 (11개 규칙) + JSON Schema 검증
        ↓
Playwright UI 테스트 (login/signup/cart) → 51 passed
        ↓
pytest API 테스트 (login API) → 6 passed  ← Day 22 추가
```

## 다음 단계 (Day 23~)
- API 테스트 범위 확장 (회원가입, 상품 목록 등)
- GitHub Actions CI/CD 연동
- 성능 테스트 (Locust)