# Day 26 Summary: 웹 UI + Playwright E2E + CI 3단 분리 + Docker

## 작업 날짜
2026-10-28

## 목표
포트폴리오에 바로 보여줄 수 있는 수준으로 완성
- 로드맵 1단계(보여주기): 웹 UI
- 로드맵 2단계(스스로 검증하기): 이 도구 자체를 E2E까지 테스트하고 CI 연동

## 작업 내용

### 1. 웹 UI (app/static/)
- 입력 방식 2가지: 요구사항으로 생성 / TC JSON 붙여넣어 검증
- 결과: PASS·FAIL 판정, 지표(규칙 통과 수, Schema 오류, Negative, Edge, Regression 수)
- 결과 탭: 검증 결과 / 테스트 케이스 / 리포트 / Playwright / JSON, 복사·다운로드
- 라이트/다크 모드, 모바일 대응, 키보드 탭 이동, Ctrl+Enter 실행
- 외부 라이브러리 없음. 모든 문자열은 textContent로 넣어 XSS 차단

### 2. 서버
- `GET /`: 웹 UI 제공
- `POST /api/analyze`: TC JSON → 검증 + 리포트 + Playwright 한 번에

### 3. Playwright 코드 생성 버그 수정
- 기능명에 따옴표가 있으면 생성된 TypeScript가 문법 오류
- 스텝에 줄바꿈이 있으면 주석 밖으로 코드가 새어 나감
- 필드가 리스트가 아니면 글자 단위로 반복
→ JS 문자열 이스케이프, 주석 텍스트 한 줄 처리, 리스트 타입 확인 추가

### 4. E2E 테스트 25개 × 2 (데스크톱 + 모바일)
- Page Object 패턴 (tests/e2e/pages/QaAgentPage.ts)
- data-testid 선택자, 고정 대기 없음
- page.route로 502 / 500 / 422 / 연결 실패 / 느린 응답 재현
- XSS, 키보드 접근성, 가로 스크롤 없음 검증
- `--repeat-each=3`으로 150/150 통과 → flaky 없음 확인

### 5. CI 3단 분리
- unit-api / e2e / external-api
- 실패 시 어느 단계 문제인지 바로 구분, 외부 서비스 장애와 내 코드 문제 분리

### 6. Docker, .env.example
- `docker run -p 8000:8000 qa-agent` → mock 모드로 바로 실행
- non-root 사용자, HEALTHCHECK 포함

## 결과
| 구분 | 개수 | 결과 |
|------|------|------|
| 단위 (pytest) | 29 | PASS |
| API (pytest) | 23 | PASS |
| E2E (Playwright) | 50 (25 × 2) | PASS, 3회 반복 150/150 |

## 면접 설명 포인트
- "도구 자체를 테스트 피라미드(단위 / API / E2E)로 검증했습니다."
- "장애 상황은 실제로 만들기 어려워서 네트워크 모킹으로 결정적으로 재현했습니다."
- "flaky를 막으려고 고정 대기 대신 자동 재시도 assertion을 쓰고, 반복 실행으로 안정성을 확인했습니다."
- "AI나 사용자가 넣은 문자열이 화면이나 생성 코드를 깨지 않도록 XSS / 코드 주입을 테스트로 고정했습니다."

## 다음 단계
- 로드맵 3단계: PR에서 요구사항 문서가 바뀌면 TC 생성 + 검증 결과를 PR 코멘트로 남기는 GitHub Action
- 로드맵 4단계: 결함을 심은 데모 앱으로 AI 생성 테스트의 결함 검출률 측정
