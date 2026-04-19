# QA Agent MVP

> 요구사항 문서를 입력받아 Claude API로 테스트 케이스를 자동 생성하고,
> 구조/품질 검증을 거쳐 Playwright 자동화 테스트 코드까지 변환하는 end-to-end QA 파이프라인

---

## 1. 프로젝트 소개

실무에서 요구사항 분석과 테스트 케이스 작성은 시간이 많이 들고, 사람마다 품질 편차가 큽니다.

이 프로젝트는 **Claude API를 연동하여 요구사항을 입력하면 테스트 케이스 JSON을 자동 생성하고, 커스텀 검증 + JSON Schema 검증 + markdown 리포트 자동 생성 + Playwright 테스트 코드 변환까지 명령어 한 번으로 실행**되는 QA 자동화 파이프라인입니다.

---

## 2. 전체 파이프라인

```
요구사항 문서 (sample_inputs/*.md)
        ↓
Claude API 호출 (generate_test_case.py)
        ↓
테스트 케이스 JSON 자동 생성 (sample_outputs/*.json)
        ↓
커스텀 품질 검증 (validate_test_case.py) ──→ 11개 규칙 검사
        ↓
JSON Schema 검증 (schema_validate_test_case.py)
        ↓
markdown 리포트 자동 생성 (sample_reports/*.md)
        ↓
Playwright 테스트 코드 자동 생성 (playwright/*.spec.ts)
```

**end-to-end 실행 (명령어 한 번):**
```bash
python app/run_pipeline.py sample_inputs/login_requirement.md
```

---

## 3. 주요 기능

### 3-1. 테스트 케이스 자동 생성
- 요구사항 문서를 입력하면 Claude API를 호출하여 JSON 형태의 테스트 케이스 자동 생성
- 프롬프트 템플릿 기반으로 Happy Path / Negative Case / Edge Case 포함

### 3-2. 커스텀 품질 검증 (11개 규칙)
| 번호 | 검사 항목 |
|------|----------|
| 1 | 필수 필드 존재 여부 |
| 2 | 필수 문자열 필드 공백 여부 |
| 3 | 필수 리스트 필드 공백 여부 |
| 4 | priority / risk_level 허용값 여부 |
| 5 | traceability 형식 여부 |
| 6 | negative_cases / edge_cases 교차 중복 여부 |
| 7 | test_steps / expected_results 최소 개수 여부 |
| 8 | traceability 내부 중복 여부 |
| 9 | preconditions / test_steps / expected_results 내부 중복 여부 |
| 10 | negative_cases 내부 중복 여부 |
| 11 | edge_cases 내부 중복 여부 |

### 3-3. JSON Schema 검증
- `schemas/test_case.schema.json` 기준으로 구조 검증
- jsonschema 라이브러리 (Draft7Validator) 사용

### 3-4. 검증 리포트 자동 생성
- 검증 결과를 markdown 리포트로 자동 저장
- `sample_reports/*_validation_report.md`

### 3-5. Playwright 테스트 코드 자동 생성
- 테스트 케이스 JSON에서 Playwright TypeScript 코드 자동 생성
- Happy Path / Negative Cases / Edge Cases 구조로 scaffold 생성
- 실제 동작 검증 구현 (Happy Path, Negative 1~2)

```typescript
test('Happy Path - 정상 동작 확인', async ({ page }) => {
  await page.goto(`${BASE_URL}/login`);
  await page.fill('#username', 'tomsmith');
  await page.fill('#password', 'SuperSecretPassword!');
  await page.click('button[type="submit"]');
  await expect(page).toHaveURL(`${BASE_URL}/secure`);
  await expect(page.locator('.flash.success')).toBeVisible();
});
```

---

## 4. 실행 방법

### 환경 설정
```bash
# Python 패키지 설치
pip install -r requirements.txt

# .env 파일 생성
ANTHROPIC_API_KEY=your_api_key_here

# Playwright 설치
npm install -D @playwright/test
npx playwright install
```

### 실행

```bash
# end-to-end 파이프라인 (생성 + 검증 한 번에)
python app/run_pipeline.py sample_inputs/login_requirement.md

# 개별 실행
python app/generate_test_case.py sample_inputs/login_requirement.md
python app/validate_test_case.py sample_outputs/login_test_case.json
python app/schema_validate_test_case.py sample_outputs/login_test_case.json
python app/generate_report.py sample_outputs/login_test_case.json
python app/generate_playwright.py sample_outputs/login_test_case.json

# Playwright 테스트 실행
npx playwright test playwright/login.spec.ts --headed
npx playwright test playwright/login.spec.ts --reporter=html
```

---

## 5. 폴더 구조

```
qa-agent-mvp/
├── app/
│   ├── main.py                      # 프롬프트 조립
│   ├── generate_test_case.py        # Claude API 연동 TC 자동 생성
│   ├── validate_test_case.py        # 커스텀 품질 검증 (11개 규칙)
│   ├── schema_validate_test_case.py # JSON Schema 검증
│   ├── generate_report.py           # 검증 리포트 자동 생성
│   ├── generate_playwright.py       # Playwright 코드 자동 생성
│   └── run_pipeline.py              # end-to-end 파이프라인
├── docs/                            # 일별 작업 summary
├── playwright/                      # 생성된 Playwright 테스트 코드
├── prompts/                         # 프롬프트 템플릿
├── sample_inputs/                   # 요구사항 문서
├── sample_outputs/                  # 생성된 테스트 케이스 JSON
├── sample_reports/                  # 검증 리포트
├── schemas/                         # JSON Schema 정의
├── requirements.txt
└── .env.example
```

---

## 6. 기술 스택

| 구분 | 기술 |
|------|------|
| AI | Claude API (Anthropic SDK, claude-sonnet-4-5) |
| 언어 | Python, TypeScript |
| 테스트 자동화 | Playwright |
| 검증 | jsonschema (Draft7Validator) |
| 버전 관리 | Git, GitHub |

---

## 7. 샘플 입력 / 출력

### 입력 (sample_inputs/login_requirement.md)
```markdown
# 로그인 기능 요구사항
- 이메일/비밀번호 기반 로그인
- 잘못된 정보 입력 시 오류 메시지 표시
- 로그인 성공 시 메인 페이지 이동
```

### 출력 (sample_outputs/login_test_case.json)
```json
{
  "feature_name": "사용자 로그인",
  "priority": "P0",
  "risk_level": "High",
  "test_steps": [...],
  "expected_results": [...],
  "negative_cases": [...],
  "edge_cases": [...],
  "traceability": ["REQ-LOGIN-001: ..."]
}
```

### 파이프라인 실행 결과
```
==================================================
QA Agent MVP - End-to-End Pipeline
==================================================
[Step 1] 테스트 케이스 생성
  - Claude API 호출 중...
  - 저장 완료: sample_outputs/login_test_case.json
[Step 2] 커스텀 검증
  [PASS] 필수 필드 존재
  [PASS] traceability 형식
  ...
[Step 3] Schema 검증
  [PASS] JSON Schema 검증
==================================================
최종 결과: PASS ✅
==================================================
```

---

## 8. 향후 계획

| 단계 | 내용 |
|------|------|
| 단기 | 회원가입 / 장바구니 Playwright 실제 구현 |
| 단기 | Negative / Edge Case 전체 구현 |
| 중기 | API 테스트 자동화 추가 (pytest + requests) |
| 중기 | 데이터 드리븐 테스트 리팩토링 |
| 장기 | CI/CD 파이프라인 연동 (GitHub Actions) |
| 장기 | 성능 테스트 추가 (Locust) |

---

## 9. 작업 이력

| Day | 작업 내용 |
|-----|----------|
| Day 1~12 | 프롬프트 파이프라인 구성, 테스트 케이스 JSON 설계, validator 구현 |
| Day 13 | negative/edge_cases 내부 중복 검사 추가 |
| Day 14 | JSON Schema 정식 검증 도입 |
| Day 15 | Claude API 연동 테스트 케이스 자동 생성 |
| Day 16 | end-to-end 파이프라인 구현 |
| Day 17 | 검증 결과 markdown 리포트 자동 생성 |
| Day 18 | Playwright 테스트 코드 자동 생성 및 실제 구현 |