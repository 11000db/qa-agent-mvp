// TC v2 (Day 24 이후, Knowledge Injection 적용): sample_outputs/login_test_case.json
import { test, expect, Shop, ACCOUNT_V2 as A, excluded } from '../shop';

test.describe('로그인 v2 - 정상 흐름', () => {
  test('[ER1] 로그인 후 메인 페이지로 이동한다', { tag: '@happy' }, async ({ page }) => {
    await new Shop(page).login(A.email, A.password);
    await expect(page).toHaveURL(/\/shop$/, { timeout: 3000 });
  });

  test('[ER2] 페이지 상단에 사용자 이름 또는 이메일이 표시된다', { tag: '@happy' }, async ({ page }) => {
    await new Shop(page).login(A.email, A.password);
    await expect(page.locator('header')).toContainText(new RegExp(`${A.name}|${A.email}`));
  });

  test('[ER3] 브라우저 쿠키에 인증 정보가 저장된다', { tag: '@happy' }, async ({ page, context }) => {
    await new Shop(page).login(A.email, A.password);
    await new Shop(page).expectLoggedIn();
    expect((await context.cookies()).length).toBeGreaterThan(0);
  });

  test('[ER4] 로그인 상태로 로그인 페이지에 접근하면 메인으로 이동한다', { tag: '@happy' }, async ({ page }) => {
    await new Shop(page).login(A.email, A.password);
    await page.goto('/shop/login');
    await expect(page).toHaveURL(/\/shop$/);
  });

  test('[ER5] 비밀번호 입력란은 마스킹되어 평문이 노출되지 않는다', { tag: '@happy' }, async ({ page }) => {
    await page.goto('/shop/login');
    await expect(new Shop(page).passwordInput()).toHaveAttribute('type', 'password');
  });
});

test.describe('로그인 v2 - Negative', () => {
  test('[N1] 잘못된 비밀번호면 오류 메시지가 표시되고 로그인에 실패한다', async ({ page }) => {
    const shop = new Shop(page);
    await shop.login(A.email, 'WrongPass1!');
    await expect(page.getByText('이메일 또는 비밀번호가 올바르지 않습니다')).toBeVisible();
    await shop.expectLoggedOut();
  });

  test('[N2] 존재하지 않는 이메일이면 오류 메시지가 표시되고 로그인에 실패한다', async ({ page }) => {
    const shop = new Shop(page);
    await shop.login('nobody@example.com', 'Test1234!');
    await expect(page.getByText('이메일 또는 비밀번호가 올바르지 않습니다')).toBeVisible();
    await shop.expectLoggedOut();
  });

  test('[N3] 이메일을 비우면 "이메일을 입력해주세요"가 표시된다', async ({ page }) => {
    await new Shop(page).login('', A.password);
    await expect(page.getByText('이메일을 입력해주세요')).toBeVisible();
  });

  test('[N4] 비밀번호를 비우면 "비밀번호를 입력해주세요"가 표시된다', async ({ page }) => {
    await new Shop(page).login(A.email, '');
    await expect(page.getByText('비밀번호를 입력해주세요')).toBeVisible();
  });

  test('[N5] 이메일 형식이 아니면(testexample.com) 형식 오류 메시지가 표시된다', async ({ page }) => {
    await new Shop(page).login('testexample.com', A.password);
    await expect(page.getByText(/올바른 이메일 형식/)).toBeVisible();
  });

  test('[N6] 5회 연속 실패하면 계정 잠금 또는 CAPTCHA 요구 메시지가 표시된다', async ({ page }) => {
    const shop = new Shop(page);
    for (let i = 0; i < 5; i++) await shop.login(A.email, `Wrong${i}!`);
    await expect(page.getByText(/잠금|잠겼|CAPTCHA|자동입력/)).toBeVisible();
  });

  test("[N7] SQL Injection(' OR '1'='1) 시도는 차단되고 정상적인 오류 메시지가 표시된다", async ({ page }) => {
    const shop = new Shop(page);
    await shop.login(A.email, "' OR '1'='1");
    await expect(page.getByText('이메일 또는 비밀번호가 올바르지 않습니다')).toBeVisible();
    await shop.expectLoggedOut();
  });
});

test.describe('로그인 v2 - Edge', () => {
  test('[E1] 이메일 앞뒤 공백은 trim되어 정상 로그인된다', async ({ page }) => {
    const shop = new Shop(page);
    await shop.login(` ${A.email} `, A.password);
    await shop.expectLoggedIn();
  });

  test('[E2] 비밀번호 앞뒤 공백은 그대로 인증되어 실패한다', async ({ page }) => {
    const shop = new Shop(page);
    await shop.login(A.email, ` ${A.password} `);
    await shop.expectLoggedOut();
  });

  excluded('not-automatable', 'E3', 'Caps Lock 상태에서 경고 메시지가 표시된다', '브라우저 자동화로 Caps Lock 상태를 재현할 수 없음');
  excluded('not-automatable', 'E4', '로그인 버튼 연속 클릭 시 1회만 처리된다', '서버 처리 횟수를 관찰할 수단이 없음');
  excluded('out-of-scope', 'E5', '네트워크가 끊기면 타임아웃 메시지가 표시된다', '요구사항에 없는 클라이언트 네트워크 처리');
  excluded('out-of-scope', 'E6', '세션 만료 후 재로그인 시 이전 페이지로 이동한다', '요구사항에 세션 만료 정책 없음');

  test('[E7][Regression] 로그아웃 후 재로그인 시 세션이 새로 생성되고 이전 데이터가 남지 않는다', async ({ page }) => {
    const shop = new Shop(page);
    await shop.login(A.email, A.password);
    await shop.addToCart('PRD-001');
    await shop.logout();
    await shop.expectLoggedOut();
    await shop.login(A.email, A.password);
    await shop.expectLoggedIn();
    await expect(shop.cartBadge()).toHaveText('장바구니 (0)');
  });

  excluded('out-of-scope', 'E8', '[Regression] 비밀번호 변경 후 이전 비밀번호로 로그인하면 실패한다', '요구사항에 비밀번호 변경 기능 없음');

  test('[E9] 254자 이메일은 정상 처리되거나 명확한 메시지가 표시된다', async ({ page }) => {
    const shop = new Shop(page);
    const email = `${'a'.repeat(254 - '@example.com'.length)}@example.com`;
    await shop.login(email, A.password);
    await expect(page.getByText(/올바르지 않습니다|자 이하|길이/)).toBeVisible();
  });

  test('[E10] 128자 비밀번호는 정상 처리되거나 명확한 메시지가 표시된다', async ({ page }) => {
    const shop = new Shop(page);
    await shop.login(A.email, 'a'.repeat(128));
    await expect(page.getByText(/올바르지 않습니다|자 이하|길이/)).toBeVisible();
  });
});
