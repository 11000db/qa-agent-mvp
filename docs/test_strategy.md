# QA Agent 테스트 전략

## 1. 목적
QA Agent는 "테스트 케이스의 품질을 검증하는 도구"입니다.
검증 도구가 틀리면 잘못된 테스트 케이스가 PASS로 통과하므로, 도구 자체의 정확성이 가장 중요한 품질 목표입니다.

> 실제 사례: Day 25 이전 `run_pipeline.py`는 8~11번 중복 검사를 실행하지 않고 PASS를 출력했습니다.
> 규칙 로직이 여러 파일에 복사돼 있었기 때문이며, `core.py`로 통합하고 규칙별 테스트를 붙여 재발을 막았습니다.

## 2. 테스트 범위

| 대상 | 범위 안 | 범위 밖 |
|------|--------|--------|
| 품질 규칙 | 11개 규칙의 PASS / FAIL 판정, 엉뚱한 타입 입력 | 규칙 자체의 타당성 (사람 리뷰 영역) |
| 생성 | mock 선택 로직, live 응답 파싱 / 실패 처리 | Claude 응답 품질 (로드맵 4단계에서 측정) |
| API | 정상 응답, 오류 코드, 입력 제한 | 부하 / 성능 |
| 웹 UI | 사용자 흐름, 장애 처리, XSS, 키보드 접근성, 반응형 | 브라우저 호환성 (Chromium만) |

## 3. 테스트 레벨

### 단위 (tests/test_core.py)
- 정상 샘플 3종은 11개 규칙 + Schema 모두 PASS
- invalid 샘플 6종은 **의도한 규칙 번호**에서 FAIL (단순히 FAIL인지만 보지 않음)
- live 모드는 `call_claude_api`를 대체해서 API 비용과 네트워크 없이 파싱 / 오류 처리를 검증
- 생성 코드 이스케이프: 따옴표, 줄바꿈, `*/`가 TypeScript 문법을 깨지 않는지

### API (tests/test_server.py)
- FastAPI TestClient로 서버를 띄우지 않고 요청 / 응답 검증
- 경계값: 빈 문자열, 공백만, 20,000자 초과 → 422
- 상태: live 모드 + 키 없음 → 400, Claude 응답 파싱 실패 → 502
- 보안: `/static/../core.py` 경로 탈출 차단

### E2E (tests/e2e/)
| 파일 | 시나리오 |
|------|---------|
| home.spec.ts | 첫 화면, 샘플 로드, 글자 수, 가로 스크롤 없음 |
| pipeline.spec.ts | 생성 + 검증 PASS, 결과 탭, 다운로드, 복사, 단축키, 빈 입력, live 키 없음 |
| analyze.spec.ts | 불량 TC의 FAIL 표시, JSON 문법 오류, 배열 거부, XSS |
| resilience.spec.ts | 502 / 500 / 422 / 연결 실패 / 느린 응답과 중복 실행 방지 |
| accessibility.spec.ts | 탭 키보드 이동, 접근 가능한 이름 |

설계 원칙:
- **Page Object**: 선택자와 동작은 `pages/QaAgentPage.ts`에만 둔다
- **`data-testid`**: 스타일 / 문구 변경에 깨지지 않는 선택자
- **고정 대기 금지**: `waitForTimeout` 대신 web-first assertion(`toHaveText` 등)의 자동 재시도 사용
- **네트워크 모킹**: 장애 상황은 `page.route`로 결정적으로 재현
- **서버 요청 여부 검증**: 클라이언트에서 막아야 하는 입력은 요청이 나가지 않았는지까지 확인
- **두 개 프로젝트**: 데스크톱(Desktop Chrome)과 모바일(Pixel 7)에서 같은 시나리오 실행

## 4. 실행 환경
- 모든 자동 테스트는 **mock 모드**로 실행 → API 키, 비용, 외부 네트워크 의존 없음
- E2E는 `playwright.config.ts`의 `webServer`가 서버를 자동으로 띄움 (`ANTHROPIC_API_KEY` 비움)

## 5. CI (.github/workflows/test.yml)
| Job | 내용 | 산출물 |
|-----|------|-------|
| unit-api | pytest 단위 + API | JUnit XML, HTML 리포트 |
| e2e | Playwright 데스크톱 + 모바일 | HTML 리포트, 실패 시 스크린샷 / trace |
| external-api | dummyjson 외부 API 테스트 | HTML 리포트 |

- 외부 API 테스트는 외부 서비스 장애 영향을 받으므로 별도 Job으로 분리해, 실패 원인이 내 코드인지 외부인지 바로 구분되게 했다.
- CI에서만 `retries: 1` + `trace: on-first-retry`: 재시도로 통과한 테스트는 리포트에 flaky로 표시되고 trace로 원인을 볼 수 있다.

## 6. Flaky 관리
- 로컬에서 `--repeat-each=3`으로 전체 스위트 3회 반복 → 150/150 통과 확인 (Day 26)
- 새 E2E를 추가할 때 같은 방식으로 반복 실행 후 머지

## 7. 알려진 한계 / 다음 단계
- Claude가 만든 테스트 케이스의 "내용 품질"은 아직 자동 측정하지 않는다 → 로드맵 4단계: 결함을 심은 데모 앱으로 검출률 측정
- 브라우저는 Chromium만 실행 (Firefox / WebKit은 필요 시 프로젝트 추가)
