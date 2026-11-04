# Day 24 Summary: Knowledge Injection Layer 추가

## 작업 날짜
2026-04-27

## 목표
요구사항만 보고 TC를 뽑는 수준에서 벗어나, 실무에서 겪은 문제를 프롬프트에 반영한다.
Regression 포인트가 TC에 자동으로 들어가게 만든다.

## 배경
지금까지는 요구사항을 넣으면 요구사항 범위 안의 TC만 나왔다.
그런데 실무에서 가장 자주 터지는 건 새 기능이 아니라 기존 기능이다.
새 릴리즈 때 커밋이 누락되면서 원래 되던 기능이 깨지는 경우를 여러 번 겪었고,
이건 BVT 단계에서 잡아야 한다.
그래서 TC를 만들 때 변경과 연관된 기존 기능의 Regression 포인트도 같이 나오도록 했다.

## 작업 내용

### prompts/requirement_to_test_case.md 에 Knowledge Injection Layer 추가

추가된 내용:
1. Regression 포인트 필수 포함
   - 신규 기능 TC 외에 변경사항과 연관된 기존 기능 regression 포인트 포함
   - [Regression] 태그로 구분
2. 상태 전이 케이스 포함
   - A → B → A 상태 전이 케이스 필수 포함
   - 중간 예외 발생 시 상태 복구 검증
3. 경계값 및 예외 처리
   - 최솟값, 최댓값, 경계값 포함
   - 네트워크 단절, 전원 차단 등 비정상 종료 후 재기동 시 동작 포함

## 결과

login_requirement.md 파이프라인 실행 결과:

edge_cases에 Regression 태그 포함:
- [Regression] 로그아웃 후 재로그인 시 세션이 정상적으로 재생성되고 이전 세션 데이터가 남아있지 않다
- [Regression] 비밀번호 변경 후 이전 비밀번호로 로그인 시도 시 로그인이 실패한다

notes에 Regression 태그 포함:
- [Regression] 비밀번호 변경, 계정 탈퇴 후 재가입 시나리오와 연계 테스트 필요

signup, cart 파이프라인에서도 Regression 태그 정상 포함 확인

## 정리
생성 결과에 [Regression] 항목이 들어가는 건 확인했다.
다만 이 항목들이 실제 결함을 더 잘 잡는지는 아직 모른다. 숫자로 확인할 방법이 필요하다.
(→ Day 27에서 결함 주입으로 측정)

## 다음 단계 (Day 25~)
- Knowledge Injection Layer 고도화
- 도메인별 노하우 추가 (금융, 의료기기 등)
- README 업데이트