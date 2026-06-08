# Day 24 Summary: Knowledge Injection Layer 추가

## 작업 날짜
2026-04-27

## 목표
단순 TC 생성기를 넘어 실무 QA 노하우가 녹아든 에이전트로 발전
Regression 포인트 자동 포함으로 차별화

## 배경
일반 TC 생성기와의 차이:
- 기존: 요구사항 넣으면 그냥 TC 뽑아줌
- 개선 후: 주영씨 실무 노하우가 녹아있어서 뽑히는 TC의 질이 다름

핵심 노하우:
새 릴리즈가 나올 때 커밋 누락으로 인해 기존에 되던 기능이 깨지는 경우가 발생한다.
이를 사전에 잡기 위한 BVT 관점의 Regression TC가 자동으로 포함되어야 한다.

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

## 면접 설명 포인트
"단순 TC 생성이 아니라 실무 경험에서 나온 QA 노하우를 프롬프트에 녹였습니다.
새 릴리즈에서 커밋 누락으로 기존 기능이 깨지는 케이스를 사전에 잡기 위해
Regression 포인트가 자동으로 포함됩니다."

## 다음 단계 (Day 25~)
- Knowledge Injection Layer 고도화
- 도메인별 노하우 추가 (금융, 의료기기 등)
- README 업데이트