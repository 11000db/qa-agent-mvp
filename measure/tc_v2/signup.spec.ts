// TC v2 (Day 24 이후): sample_outputs/signup_test_case.json
// 절차 변환: 가입 이메일은 실행마다 중복되지 않도록 고유값을 쓴다 (TC: test_new_user@example.com)
import { test, expect, Shop, DUPLICATE_EMAIL_V2, excluded, uniqueEmail } from '../shop';

const NAME = '홍길동';
const PASSWORD = 'Password123!';

test.describe('회원가입 v2 - 정상 흐름', () => {
  test('[ER1] 회원가입 버튼 클릭 후 3초 이내 응답이 반환된다', { tag: '@happy' }, async ({ page }) => {
    const shop = new Shop(page);
    await shop.signup(NAME, uniqueEmail('v2'), PASSWORD);
    await expect(page.getByText(/회원가입이 완료되었습니다|환영합니다/)).toBeVisible({ timeout: 3000 });
  });

  test('[ER2] "회원가입이 완료되었습니다" 또는 "환영합니다" 메시지가 표시된다', { tag: '@happy' }, async ({ page }) => {
    const shop = new Shop(page);
    await shop.signup(NAME, uniqueEmail('v2'), PASSWORD);
    await shop.expectSignupSucceeded();
  });

  test('[ER3] 로그인 페이지 또는 메인 페이지로 자동 이동된다', { tag: '@happy' }, async ({ page }) => {
    await new Shop(page).signup(NAME, uniqueEmail('v2'), PASSWORD);
    await expect(page).toHaveURL(/\/shop(\/login)?$/);
  });

  excluded('not-automatable', 'ER4', 'DB에 신규 사용자 레코드가 생성된다', 'DB 직접 조회 필요');
  excluded('not-automatable', 'ER5', '비밀번호는 암호화되어 저장된다', 'DB 직접 조회 필요');
});

test.describe('회원가입 v2 - Negative', () => {
  test('[N1] 이름을 비우면 "이름을 입력해주세요"가 표시된다', async ({ page }) => {
    await new Shop(page).signup('', uniqueEmail('v2'), PASSWORD);
    await expect(page.getByText('이름을 입력해주세요')).toBeVisible();
  });

  test('[N2] 이메일을 비우면 "이메일을 입력해주세요"가 표시된다', async ({ page }) => {
    await new Shop(page).signup(NAME, '', PASSWORD);
    await expect(page.getByText('이메일을 입력해주세요')).toBeVisible();
  });

  test('[N3] 비밀번호를 비우면 "비밀번호를 입력해주세요"가 표시된다', async ({ page }) => {
    await new Shop(page).signup(NAME, uniqueEmail('v2'), '');
    await expect(page.getByText('비밀번호를 입력해주세요')).toBeVisible();
  });

  test('[N4] 모든 필드를 공백으로 입력하면 각 필드별 오류 메시지가 표시된다', async ({ page }) => {
    const shop = new Shop(page);
    await shop.signup(' ', ' ', ' ');
    for (const field of ['name', 'email', 'password']) {
      await expect(page.locator(`#${field}-error`)).toBeVisible();
    }
  });

  test('[N5] 이미 가입된 이메일이면 "이미 사용 중인 이메일입니다"가 표시되고 가입이 차단된다', async ({ page }) => {
    const shop = new Shop(page);
    await shop.signup(NAME, DUPLICATE_EMAIL_V2, PASSWORD);
    await expect(page.getByText('이미 사용 중인 이메일입니다')).toBeVisible();
    await shop.expectSignupBlocked();
  });

  test("[N6] 7자 비밀번호('Pass123')면 8자 이상 안내가 표시된다", async ({ page }) => {
    await new Shop(page).signup(NAME, uniqueEmail('v2'), 'Pass123');
    await expect(page.getByText(/8자 이상/).first()).toBeVisible();
    await new Shop(page).expectSignupBlocked();
  });

  test("[N7] 잘못된 이메일 형식('invalid-email')이면 형식 오류가 표시된다", async ({ page }) => {
    await new Shop(page).signup(NAME, 'invalid-email', PASSWORD);
    await expect(page.getByText(/올바른 이메일 형식/)).toBeVisible();
  });

  test("[N8] 잘못된 이메일 형식('test@')이면 유효성 검사 실패 메시지가 표시된다", async ({ page }) => {
    await new Shop(page).signup(NAME, 'test@', PASSWORD);
    await expect(page.getByText(/올바른 이메일 형식/)).toBeVisible();
  });

  test("[N9] SQL Injection(admin' OR '1'='1)은 검증 실패 또는 안전하게 처리된다", async ({ page }) => {
    const shop = new Shop(page);
    await shop.signup(NAME, "admin' OR '1'='1", PASSWORD);
    await expect(page.getByText(/올바른 이메일 형식/)).toBeVisible();
    await shop.expectSignupBlocked();
  });

  test('[N10] XSS(<script>) 입력은 실행되지 않고 문자열로 처리된다', async ({ page }) => {
    let dialog = false;
    page.on('dialog', async (d) => { dialog = true; await d.dismiss(); });
    const shop = new Shop(page);
    await shop.signup('<script>alert(1)</script>', uniqueEmail('xss'), PASSWORD);
    await expect(page.getByText('<script>alert(1)</script>', { exact: false })).toBeVisible();
    expect(dialog).toBe(false);
  });
});

test.describe('회원가입 v2 - Edge', () => {
  test("[E1] 정확히 8자 비밀번호('Pass1234')면 가입에 성공한다", async ({ page }) => {
    const shop = new Shop(page);
    await shop.signup(NAME, uniqueEmail('v2'), 'Pass1234');
    await shop.expectSignupSucceeded();
  });

  test('[E2] 128자 비밀번호로 가입에 성공한다', async ({ page }) => {
    const shop = new Shop(page);
    await shop.signup(NAME, uniqueEmail('v2'), 'a'.repeat(128));
    await shop.expectSignupSucceeded();
  });

  excluded('no-criteria', 'E3', "이름에 특수문자('홍길동!') 입력 시 허용 여부 확인", '기대 결과(허용/거부)가 정해지지 않음');
  excluded('no-criteria', 'E4', "이름 1자('홍') 입력 시 가입 성공 여부 확인", '기대 결과가 정해지지 않음');

  test('[E5] 이름 100자 초과 입력 시 입력 제한 또는 오류 메시지가 표시된다', async ({ page }) => {
    await new Shop(page).signup('가'.repeat(101), uniqueEmail('v2'), PASSWORD);
    await expect(page.getByText(/이름.*(자 이하|길이|초과)/)).toBeVisible();
  });

  excluded('no-criteria', 'E6', '이메일 최대 길이(254자) 입력 시 처리 확인', '기대 결과가 정해지지 않음');
  excluded('no-criteria', 'E7', "대소문자가 다른 같은 이메일('Test@'/'test@') 중복 처리 확인", '중복으로 볼지 기대 결과가 정해지지 않음');
  excluded('not-automatable', 'E8', '회원가입 버튼 연속 2회 클릭 시 중복 계정 생성 방지', '서버 처리 횟수를 관찰할 수단이 없음');

  test('[E9][Regression] 가입 직후 같은 이메일로 다시 가입하면 중복 오류가 발생한다', async ({ page }) => {
    const shop = new Shop(page);
    const email = uniqueEmail('dup');
    await shop.signup(NAME, email, PASSWORD);
    await shop.expectSignupSucceeded();
    await shop.signup(NAME, email, PASSWORD);
    await expect(page.getByText('이미 사용 중인 이메일입니다')).toBeVisible();
  });

  test('[E10][Regression] 가입 후 로그인이 정상 동작한다', async ({ page }) => {
    const shop = new Shop(page);
    const email = uniqueEmail('login');
    await shop.signup(NAME, email, PASSWORD);
    await shop.expectSignupSucceeded();
    await shop.login(email, PASSWORD);
    await shop.expectLoggedIn();
  });

  excluded('out-of-scope', 'E11', '가입 중 네트워크 단절 시 타임아웃 메시지가 표시된다', '요구사항에 없는 클라이언트 네트워크 처리');
  excluded('not-automatable', 'E12', '가입 요청 중 새로고침 시 중복 요청 방지', '서버 처리 횟수를 관찰할 수단이 없음');

  test('[E13] 입력 중 페이지를 벗어났다가 다시 들어오면 입력값이 초기화된다', async ({ page }) => {
    const shop = new Shop(page);
    await page.goto('/shop/signup');
    await shop.nameInput().fill(NAME);
    await shop.emailInput().fill('draft@example.com');
    await page.goto('/shop');
    await page.goto('/shop/signup');
    await expect(shop.nameInput()).toHaveValue('');
    await expect(shop.emailInput()).toHaveValue('');
  });
});
