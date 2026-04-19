# Day 18 Summary: Playwright 테스트 코드 자동 생성

## 작업 날짜
2026-04-20

## 목표
테스트 케이스 JSON을 읽어 Playwright TypeScript 테스트 코드 skeleton을 자동 생성

## 작업 내용

### 1. app/generate_playwright.py 생성
- sample_outputs/*_test_case.json 읽기
- test_steps, expected_results, negative_cases, edge_cases 기반으로 .spec.ts 자동 생성
- playwright/ 폴더에 저장

### 2. 생성 구조
```
sample_outputs/login_test_case.json
        ↓
app/generate_playwright.py
        ↓
playwright/login.spec.ts
```

### 3. 생성된 코드 구조
```typescript
test.describe('기능명', () => {
  test('Happy Path', async ({ page }) => {
    // test_steps 주석으로 삽입
    // expected_results TODO로 삽입
  });

  test.describe('Negative Cases', () => {
    // negative_cases 케이스별 test 블록 생성
  });

  test.describe('Edge Cases', () => {
    // edge_cases 케이스별 test 블록 생성
  });
});
```

### 4. 테스트 환경
- BASE_URL: https://the-internet.herokuapp.com
- Playwright 1.59.1

## 실행 방법
```powershell
python app/generate_playwright.py sample_outputs/login_test_case.json
```

## 결과물
- playwright/login.spec.ts 자동 생성
- Happy Path 1개 + Negative Cases 7개 + Edge Cases 10개

## 현재 파이프라인 구조
| 단계 | 파일 | 역할 |
|------|------|------|
| 입력 | sample_inputs/*.md | 요구사항 문서 |
| 템플릿 | prompts/requirement_to_test_case.md | 프롬프트 템플릿 |
| 파이프라인 | app/run_pipeline.py | 전체 흐름 통합 실행 |
| 생성 | app/generate_test_case.py | Claude API 호출 및 JSON 저장 |
| 검증 1 | app/validate_test_case.py | 커스텀 품질 규칙 검증 |
| 검증 2 | app/schema_validate_test_case.py | JSON Schema 구조 검증 |
| 리포트 | app/generate_report.py | 검증 결과 markdown 리포트 생성 |
| Playwright | app/generate_playwright.py | Playwright 테스트 코드 자동 생성 |

## 다음 단계 (Day 19)
- README 포트폴리오용 정리
- 전체 아키텍처 다이어그램
- input/output 예시
- 향후 확장 방향 정리