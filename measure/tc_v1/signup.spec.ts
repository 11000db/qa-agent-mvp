// TC v1 (Day 24 이전): git show 10acc79~1:sample_outputs/signup_test_case.json
// 절차 변환: 가입 이메일은 실행마다 중복되지 않도록 고유값을 쓴다 (TC: newuser@example.com)
import { test, expect, Shop, DUPLICATE_EMAIL_V1, excluded, uniqueEmail } from '../shop';

const NAME = '홍길동';
const PASSWORD = 'Password123!';

test.describe('회원가입 v1 - 정상 흐름', () => {
  test('[ER1] 회원가입이 성공적으로 완료된다', { tag: '@happy' }, async ({ page }) => {
    await new Shop(page).signup(NAME, uniqueEmail('v1'), PASSWORD);
    await new Shop(page).expectSignupSucceeded();
  });

  test('[ER2] "회원가입이 완료되었습니다" 또는 "환영합니다" 메시지가 표시된다', { tag: '@happy' }, async ({ page }) => {
    await new Shop(page).signup(NAME, uniqueEmail('v1'), PASSWORD);
    await expect(page.getByText(/회원가입이 완료되었습니다|환영합니다/)).toBeVisible();
  });

  excluded('not-automatable', 'ER3', 'DB에 신규 사용자 레코드가 생성된다', 'DB 직접 조회 필요');
  excluded('not-automatable', 'ER4', '입력한 이메일로 사용자 계정이 등록된다', 'DB 직접 조회 필요');

  test('[ER5] 로그인 페이지로 이동하거나 로그인 유도 메시지가 표시된다', { tag: '@happy' }, async ({ page }) => {
    await new Shop(page).signup(NAME, uniqueEmail('v1'), PASSWORD);
    await expect(page.getByRole('link', { name: /로그인하러|로그인 하기/ }).or(page.getByRole('heading', { name: '로그인' }))).toBeVisible();
  });
});

test.describe('회원가입 v1 - Negative', () => {
  test('[N1] 이름을 비우면 "이름을 입력해주세요"가 표시된다', async ({ page }) => {
    await new Shop(page).signup('', uniqueEmail('v1'), PASSWORD);
    await expect(page.getByText('이름을 입력해주세요')).toBeVisible();
  });

  test('[N2] 이메일을 비우면 "이메일을 입력해주세요"가 표시된다', async ({ page }) => {
    await new Shop(page).signup(NAME, '', PASSWORD);
    await expect(page.getByText('이메일을 입력해주세요')).toBeVisible();
  });

  test('[N3] 비밀번호를 비우면 "비밀번호를 입력해주세요"가 표시된다', async ({ page }) => {
    await new Shop(page).signup(NAME, uniqueEmail('v1'), '');
    await expect(page.getByText('비밀번호를 입력해주세요')).toBeVisible();
  });

  test('[N4] 모든 필드를 비우면 각 필드별 오류 메시지가 모두 표시된다', async ({ page }) => {
    await new Shop(page).signup('', '', '');
    await expect(page.getByText('이름을 입력해주세요')).toBeVisible();
    await expect(page.getByText('이메일을 입력해주세요')).toBeVisible();
    await expect(page.getByText('비밀번호를 입력해주세요')).toBeVisible();
  });

  test('[N5] 이미 가입된 이메일(test@example.com)이면 "이미 사용 중인 이메일입니다"가 표시된다', async ({ page }) => {
    await new Shop(page).signup('김철수', DUPLICATE_EMAIL_V1, 'SecurePass99');
    await expect(page.getByText('이미 사용 중인 이메일입니다')).toBeVisible();
  });

  test('[N6] 7자 비밀번호(Pass123)면 8자 이상 오류 메시지가 표시된다', async ({ page }) => {
    await new Shop(page).signup('이영희', uniqueEmail('v1'), 'Pass123');
    await expect(page.getByText(/8자 이상/).first()).toBeVisible();
    await new Shop(page).expectSignupBlocked();
  });

  test('[N7] 잘못된 이메일 형식(invalid-email)이면 형식 오류 메시지가 표시된다', async ({ page }) => {
    await new Shop(page).signup('박민수', 'invalid-email', PASSWORD);
    await expect(page.getByText(/올바른 이메일 형식/)).toBeVisible();
  });

  for (const email of ['@example.com', 'user@', 'user@@example.com']) {
    test(`[N8] 잘못된 이메일 형식(${email})이면 형식 오류 메시지가 표시된다`, async ({ page }) => {
      await new Shop(page).signup(NAME, email, PASSWORD);
      await expect(page.getByText(/올바른 이메일 형식/)).toBeVisible();
    });
  }
});

test.describe('회원가입 v1 - Edge', () => {
  test('[E1] 정확히 8자 비밀번호(Passwor1)면 가입에 성공한다', async ({ page }) => {
    await new Shop(page).signup(NAME, uniqueEmail('v1'), 'Passwor1');
    await new Shop(page).expectSignupSucceeded();
  });

  test("[E2] 이름에 공백만 입력(' ')하면 유효성 검사에 실패한다", async ({ page }) => {
    await new Shop(page).signup(' ', uniqueEmail('v1'), PASSWORD);
    await new Shop(page).expectSignupBlocked();
  });

  excluded('no-criteria', 'E3', '이름 1자(김) 입력 시 처리 확인', '기대 결과가 정해지지 않음');
  excluded('no-criteria', 'E4', '이름 100자 이상 입력 시 처리 확인', '기대 결과가 정해지지 않음');
  excluded('no-criteria', 'E5', '이메일 최대 허용 길이 입력 시 처리 확인', '기대 결과가 정해지지 않음');
  excluded('no-criteria', 'E6', '비밀번호 256자 이상 입력 시 처리 확인', '기대 결과가 정해지지 않음');
  excluded('no-criteria', 'E7', "특수문자 이름(O'Neill, 김-철수)으로 가입 시도", '기대 결과가 정해지지 않음');
  excluded('no-criteria', 'E8', '대소문자가 다른 같은 이메일 중복 처리 확인', '중복으로 볼지 기대 결과가 정해지지 않음');
  excluded('not-automatable', 'E9', '회원가입 버튼 더블 클릭 시 중복 가입 방지', '서버 처리 횟수를 관찰할 수단이 없음');
  excluded('out-of-scope', 'E10', '가입 직전 네트워크가 끊기면 오류 처리', '요구사항에 없는 클라이언트 네트워크 처리');
});
