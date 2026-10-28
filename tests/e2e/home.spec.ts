import { test, expect } from './fixtures';

test.describe('첫 화면', () => {

  test('API 키가 없으면 MOCK 모드로 표시된다', async ({ qa }) => {
    await expect(qa.serverStatus).toHaveAttribute('data-state', 'mock');
    await expect(qa.serverStatus).toContainText('MOCK');
  });

  test('결과 영역은 빈 상태 안내로 시작한다', async ({ qa }) => {
    await expect(qa.emptyState).toBeVisible();
    await expect(qa.result).toBeHidden();
  });

  test('샘플 요구사항 3종이 표시되고 클릭하면 입력창이 채워진다', async ({ qa }) => {
    for (const name of ['login', 'signup', 'cart']) {
      await expect(qa.sample(name)).toBeVisible();
    }
    await qa.sample('cart').click();
    await expect(qa.requirementInput).toHaveValue(/장바구니/);
    await expect(qa.charCount).not.toHaveText('0');
  });

  test('입력 글자 수가 실시간으로 표시된다', async ({ qa }) => {
    await qa.requirementInput.fill('로그인 기능');
    await expect(qa.charCount).toHaveText('6');
  });

  test('화면 너비를 넘는 가로 스크롤이 생기지 않는다', async ({ qa, page }) => {
    await qa.generateFromSample('login');
    const overflow = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
    expect(overflow).toBeLessThanOrEqual(0);
  });
});
