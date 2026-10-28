# Day 25 Summary: 웹 API 서버 구축 (FastAPI + mock 모드)

## 작업 날짜
2026-10-27

## 목표
CLI로만 돌던 파이프라인을 웹 API로 노출해서
"URL 하나로 써볼 수 있는 도구"의 기반을 만든다 (최종 목표 1단계: 보여주기)

## 작업 내용

### 1. app/core.py: 파이프라인 핵심 로직 분리
- 생성 / 검증 / 리포트 / Playwright 변환을 print 없이 dict를 주고받는 함수로 정리
- CLI(run_pipeline.py)와 서버(server.py)가 같은 로직을 공유
- 11개 커스텀 규칙은 validate_test_case.py의 함수를 그대로 재사용 (규칙 중복 정의 제거)
- 경로를 프로젝트 루트 기준 절대 경로로 변경해서 어느 위치에서 실행해도 동작

### 2. mock 모드 추가
- `auto`: ANTHROPIC_API_KEY가 있으면 live, 없으면 mock
- `mock`: 요구사항 키워드(로그인/회원가입/장바구니)로 sample_outputs 결과를 반환
- `live`: Claude API 호출
- API 키 없이도 데모와 CI 테스트가 동작

### 3. app/server.py: FastAPI 서버
| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | /api/health | 서버 상태 |
| GET | /api/samples | 샘플 요구사항 목록 |
| POST | /api/generate | 요구사항 → TC JSON |
| POST | /api/validate | TC → 11개 규칙 + Schema 검증 |
| POST | /api/report | TC → markdown 리포트 |
| POST | /api/playwright | TC → Playwright 코드 |
| POST | /api/pipeline | 전체 한 번에 |

에러 처리:
- 빈 요구사항 / 공백만 / 20000자 초과 / 잘못된 mode → 422
- live 모드인데 API 키 없음 → 400
- Claude 응답 JSON 파싱 실패, max_tokens 잘림, API 오류 → 502

### 4. 테스트 42개 추가 + CI 연동
- tests/test_core.py: 정상 샘플 PASS, invalid 샘플이 의도한 규칙에서 FAIL, mock 키워드 선택, live 응답 파싱 (API 호출은 대체)
- tests/test_server.py: 엔드포인트별 정상/에러 응답 코드 검증
- GitHub Actions에 실행 단계 추가

## 발견한 버그
기존 run_pipeline.py는 8~11번 중복 검사를 실제로 하지 않고
`[PASS] 중복 검사` 를 무조건 출력하고 있었다.
core.py로 통합하면서 11개 규칙 모두 실제로 검사하도록 수정했다.
→ "검증 도구 자체도 검증이 필요하다"는 사례

## 실행 방법
```bash
pip install -r requirements.txt
python app/server.py          # http://127.0.0.1:8000/docs
python app/run_pipeline.py sample_inputs/cart_requirement.md --mode mock
python -m pytest tests/test_core.py tests/test_server.py -v
```

## 면접 설명 포인트
"CLI 스크립트를 서비스로 바꾸면서 로직을 core 모듈로 분리했고,
API 키 없이도 동작하는 mock 모드를 넣어 CI에서 외부 의존 없이 테스트합니다.
리팩토링 중 기존 파이프라인이 중복 검사 4개를 실제로 하지 않고 PASS를 출력하던 버그도 찾아 고쳤습니다."

## 다음 단계 (Day 26~)
- Day 26: 웹 UI (요구사항 입력 → 결과 탭 → 코드 복사/다운로드)
- Day 27: 이 사이트를 대상으로 Playwright E2E 작성 + CI 연동
