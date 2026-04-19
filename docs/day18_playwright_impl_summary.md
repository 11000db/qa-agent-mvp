# Day 18 Summary: Playwright 테스트 실제 구현

## 작업 날짜
2026-04-20

## 목표
Playwright skeleton 코드에서 실제 동작하는 테스트 코드로 구현
Happy Path, Negative Case 개념 이해 및 직접 구현

## 작업 내용

### 1. 테스트 환경
- 테스트 대상: https://the-internet.herokuapp.com
- 테스트 계정: tomsmith / SuperSecretPassword!
- Playwright 1.59.1 + @playwright/test

### 2. Happy Path 구현
올바른 계정으로 로그인 성공 시나리오 검증

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

### 3. Negative Case 구현

**Negative 1 - 존재하지 않는 계정**
```typescript
await page.fill('#username', 'wronguser');
await page.fill('#password', 'wrongpassword');
await expect(page.locator('.flash.error')).toBeVisible();
```

**Negative 2 - 올바른 아이디 + 틀린 비밀번호 + 메시지 내용 검증**
```typescript
await page.fill('#username', 'tomsmith');
await page.fill('#password', 'WrongPass123');
await expect(page.locator('.flash.error')).toBeVisible();
await expect(page.locator('.flash.error')).toContainText('Your password is invalid');
```

### 4. Happy Path vs Negative Case 개념 정리

| 구분 | 목적 | 검증 내용 |
|------|------|----------|
| Happy Path | 정상 동작 확인 | 로그인 성공 → /secure 이동, 성공 메시지 표시 |
| Negative Case | 실패 처리 확인 | 잘못된 입력 → 에러 메시지 표시, 로그인 차단 |

Negative PASS = 시스템이 비정상 입력을 올바르게 거부함
Negative FAIL = 비정상 입력을 막지 못함 = 서비스 버그

### 5. 테스트 실행 방법
```powershell
# 전체 실행
npx playwright test playwright/login.spec.ts --headed

# 특정 테스트만 실행
npx playwright test playwright/login.spec.ts -g "Negative 2"

# HTML 리포트 생성
npx playwright test playwright/login.spec.ts --reporter=html
npx playwright show-report
```

### 6. 트러블슈팅
- PowerShell 보안 정책 → Set-ExecutionPolicy RemoteSigned 설정
- @playwright/test 미설치 → npm init -y + npm install -D @playwright/test
- node_modules GitHub 업로드 → .gitignore에 node_modules/ 추가 후 git rm --cached

## 실행 결과
```
18 passed (60.0s)
- Happy Path: 실제 로그인 검증 PASS
- Negative 1: 존재하지 않는 계정 에러 메시지 검증 PASS
- Negative 2: 틀린 비밀번호 + 메시지 내용 검증 PASS
- Negative 3~7, Edge 1~10: skeleton (TODO)
```

## 다음 단계 (Day 19)
- README 포트폴리오용 정리
- 전체 아키텍처 다이어그램
- 향후 확장 방향 정리