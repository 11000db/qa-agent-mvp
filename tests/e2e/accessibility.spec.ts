import { test, expect } from './fixtures';

test.describe('접근성 / 키보드', () => {

  test('결과 탭은 화살표 키로 이동한다', async ({ qa, page }) => {
    await qa.generateFromSample('login');

    const first = page.getByTestId('result-tab-validation');
    await first.focus();
    await page.keyboard.press('ArrowRight');
    await expect(page.getByTestId('result-tab-testcase')).toHaveAttribute('aria-selected', 'true');
    await expect(page.getByTestId('tc-test_steps')).toBeVisible();

    await page.keyboard.press('End');
    await expect(page.getByTestId('result-tab-json')).toBeFocused();
    await page.keyboard.press('ArrowRight');
    await expect(first).toHaveAttribute('aria-selected', 'true');
  });

  test('입력란과 버튼은 접근 가능한 이름을 가진다', async ({ page, qa }) => {
    await expect(page.getByRole('textbox', { name: '요구사항 문서' })).toBeVisible();
    await expect(page.getByRole('combobox', { name: '생성 모드' })).toBeVisible();
    await expect(page.getByRole('button', { name: '생성 + 검증 실행' })).toBeVisible();
    await expect(page.getByRole('tab', { name: 'TC JSON 검증' })).toBeVisible();
    await expect(qa.errorMessage).toHaveAttribute('role', 'alert');
  });
});
