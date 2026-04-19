# Day 19 Summary: README 포트폴리오용 정리

## 작업 날짜
2026-04-20

## 목표
전체 프로젝트 완성도를 높이는 README 포트폴리오용 업데이트
Day 1~18까지의 작업 내용을 반영하여 면접/이직용으로 활용 가능한 수준으로 정리

## 작업 내용

### 1. README 전면 업데이트
기존 Day 12 수준의 README를 Day 18까지 반영하여 전면 재작성

### 2. 추가된 섹션
- 전체 파이프라인 다이어그램 (텍스트 형태)
- 주요 기능 상세 설명 (11개 검증 규칙 표 포함)
- 실행 방법 (환경 설정 + 개별/통합 실행)
- 기술 스택 표
- 샘플 입력/출력 예시
- 파이프라인 실행 결과 예시
- 향후 계획 표
- 작업 이력 표 (Day별)

### 3. 핵심 변경 내용
| 항목 | 기존 | 변경 후 |
|------|------|---------|
| 프로젝트 소개 | 단순 설명 | Claude API 연동 end-to-end 파이프라인 강조 |
| 기능 설명 | 목표 나열 | 실제 구현 내용 + 코드 예시 포함 |
| 실행 방법 | 없음 | 환경 설정 + 전체/개별 실행 명령어 추가 |
| 기술 스택 | 없음 | 표 형태로 정리 |
| 작업 이력 | 없음 | Day별 히스토리 추가 |

## 현재 파이프라인 구조 (최종)
| 단계 | 파일 | 역할 |
|------|------|------|
| 입력 | sample_inputs/*.md | 요구사항 문서 |
| 템플릿 | prompts/requirement_to_test_case.md | 프롬프트 템플릿 |
| 생성 | app/generate_test_case.py | Claude API 호출 및 JSON 저장 |
| 검증 1 | app/validate_test_case.py | 커스텀 품질 규칙 검증 (11개) |
| 검증 2 | app/schema_validate_test_case.py | JSON Schema 구조 검증 |
| 리포트 | app/generate_report.py | 검증 결과 markdown 리포트 생성 |
| Playwright | app/generate_playwright.py | Playwright 테스트 코드 자동 생성 |
| 통합 실행 | app/run_pipeline.py | 전체 파이프라인 한 번에 실행 |

## 다음 단계 (Day 20)
- 최종 데모 시나리오 완성
- login requirement → 파이프라인 전체 실행 → 결과 확인
- 발표 가능한 MVP 수준 완성