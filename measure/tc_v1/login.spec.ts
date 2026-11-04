// TC v1 (Day 24 이전): git show 10acc79~1:sample_outputs/login_test_case.json
import { test, expect, Shop, ACCOUNT_V1 as A, excluded } from '../shop';

test.describe('로그인 v1 - 정상 흐름', () => {
  test('[ST4] 비밀번호 입력란이 마스킹되어 평문이 보이지 않는다', { tag: '@happy' }, async ({ page }) => {
    await page.goto('/shop/login');
    await new Shop(page).passwordInput().fill(A.password);
    await expect(new Shop(page).passwordInput()).toHaveAttribute('type', 'password');
  });

  test('[ER1] 로그인 성공 후 메인 페이지 또는 대시보드로 이동한다', { tag: '@happy' }, async ({ page }) => {
    await new Shop(page).login(A.email, A.password);
    await expect(page).toHaveURL(/\/shop$/);
  });

  test('[ER2] 화면 상단에 사용자 이름 또는 이메일이 표시된다', { tag: '@happy' }, async ({ page }) => {
    await new Shop(page).login(A.email, A.password);
    await expect(page.locator('header')).toContainText(new RegExp(`${A.name}|${A.email}`));
  });

  test('[ER3] 로그인 세션 또는 인증 토큰이 쿠키/로컬스토리지에 저장된다', { tag: '@happy' }, async ({ page, context }) => {
    await new Shop(page).login(A.email, A.password);
    await new Shop(page).expectLoggedIn();
    expect((await context.cookies()).length).toBeGreaterThan(0);
  });

  test('[ER4] 비밀번호 입력 필드는 항상 마스킹된다', { tag: '@happy' }, async ({ page }) => {
    await new Shop(page).login(A.email, 'WrongPass123');
    await expect(new Shop(page).passwordInput()).toHaveAttribute('type', 'password');
  });
});

test.describe('로그인 v1 - Negative', () => {
  test("[N1] 잘못된 비밀번호('WrongPass123')면 오류 메시지가 표시되고 로그인에 실패한다", async ({ page }) => {
    const shop = new Shop(page);
    await shop.login(A.email, 'WrongPass123');
    await expect(page.getByText('이메일 또는 비밀번호가 올바르지 않습니다')).toBeVisible();
    await shop.expectLoggedOut();
  });

  test('[N2] 존재하지 않는 이메일이면 오류 메시지가 표시되고 로그인에 실패한다', async ({ page }) => {
    const shop = new Shop(page);
    await shop.login('nonexistent@example.com', 'AnyPassword123');
    await expect(page.getByText('이메일 또는 비밀번호가 올바르지 않습니다')).toBeVisible();
    await shop.expectLoggedOut();
  });

  test("[N3] 이메일 형식이 아니면('invalidemail.com') 유효성 검사 메시지가 표시된다", async ({ page }) => {
    await new Shop(page).login('invalidemail.com', A.password);
    await expect(page.getByText(/올바른 이메일 형식/)).toBeVisible();
  });

  test('[N4] 이메일을 비우고 로그인하면 "이메일을 입력해주세요"가 표시된다', async ({ page }) => {
    await new Shop(page).login('', A.password);
    await expect(page.getByText('이메일을 입력해주세요')).toBeVisible();
  });

  test('[N5] 비밀번호를 비우고 로그인하면 "비밀번호를 입력해주세요"가 표시된다', async ({ page }) => {
    await new Shop(page).login(A.email, '');
    await expect(page.getByText('비밀번호를 입력해주세요')).toBeVisible();
  });

  test('[N6] 둘 다 비우고 로그인하면 이메일과 비밀번호 입력 경고가 표시된다', async ({ page }) => {
    await new Shop(page).login('', '');
    await expect(page.getByText('이메일을 입력해주세요')).toBeVisible();
    await expect(page.getByText('비밀번호를 입력해주세요')).toBeVisible();
  });
});

test.describe('로그인 v1 - Edge', () => {
  test('[E1] 이메일 앞뒤 공백은 트림되어 로그인에 성공한다', async ({ page }) => {
    const shop = new Shop(page);
    await shop.login(` ${A.email} `, A.password);
    await shop.expectLoggedIn();
  });

  test("[E2] 특수문자, 공백, 한글이 섞인 비밀번호('Test 1234!@한글')도 정상 처리된다", async ({ page }) => {
    // 사전 조건: 해당 비밀번호의 계정이 있어야 해서 회원가입으로 만든다
    const shop = new Shop(page);
    const email = `unicode.${Date.now()}.${Math.random().toString(36).slice(2, 6)}@example.com`;
    await shop.signup('유니코드', email, 'Test 1234!@한글');
    await shop.login(email, 'Test 1234!@한글');
    await shop.expectLoggedIn();
  });

  test('[E3] 254자 이메일은 정상 처리되거나 길이 제한 메시지가 표시된다', async ({ page }) => {
    const email = `${'a'.repeat(254 - '@example.com'.length)}@example.com`;
    await new Shop(page).login(email, A.password);
    await expect(page.getByText(/올바르지 않습니다|자 이하|길이/)).toBeVisible();
  });

  test('[E4] 128자 비밀번호는 정상 처리되거나 길이 제한 메시지가 표시된다', async ({ page }) => {
    await new Shop(page).login(A.email, 'a'.repeat(128));
    await expect(page.getByText(/올바르지 않습니다|자 이하|길이/)).toBeVisible();
  });

  test('[E5] 5회 이상 연속 실패하면 계정 잠금 또는 CAPTCHA가 적용된다', async ({ page }) => {
    const shop = new Shop(page);
    for (let i = 0; i < 5; i++) await shop.login(A.email, `Wrong${i}!`);
    await expect(page.getByText(/잠금|잠겼|CAPTCHA|자동입력/)).toBeVisible();
  });

  excluded('not-automatable', 'E6', '로그인 버튼을 빠르게 두 번 눌러도 한 번만 처리된다', '서버 처리 횟수를 관찰할 수단이 없음');
  excluded('out-of-scope', 'E7', '느린 네트워크에서 로딩 인디케이터가 표시된다', '서버 렌더링 앱이라 클라이언트 로딩 표시 없음');
});
