import { readFileSync } from 'fs';
import { test, expect } from './fixtures';

test.describe('요구사항 → 생성 + 검증 (mock)', () => {

  test('로그인 샘플은 11개 규칙과 Schema 검증을 모두 통과한다', async ({ qa }) => {
    await qa.generateFromSample('login');

    await expect(qa.verdict).toHaveText('PASS');
    await expect(qa.featureName).not.toBeEmpty();
    await expect(qa.ruleRows).toHaveCount(11);
    await expect(qa.page.locator('[data-testid="rule-row"][data-passed="false"]')).toHaveCount(0);
    await expect(qa.metric('rules')).toHaveText('11/11');
    await expect(qa.metric('schema')).toHaveText('0');
    await expect(qa.schemaResult).toHaveText('PASS');
  });

  test('Day 24 Knowledge Injection: Regression 항목이 집계된다', async ({ qa }) => {
    await qa.generateFromSample('login');
    await expect(qa.metric('regression')).not.toHaveText('0');
  });

  test('결과 탭에서 테스트 케이스 / 리포트 / Playwright 코드를 볼 수 있다', async ({ qa }) => {
    await qa.generateFromSample('signup');

    await qa.openResultTab('testcase');
    await expect(qa.page.getByTestId('tc-test_steps')).toBeVisible();
    await expect(qa.page.getByTestId('tc-negative_cases')).toBeVisible();

    await qa.openResultTab('report');
    await expect(qa.output('report')).toContainText('# QA Validation Report');

    await qa.openResultTab('playwright');
    await expect(qa.output('playwright')).toContainText("from '@playwright/test'");

    await qa.openResultTab('json');
    await expect(qa.output('json')).toContainText('"feature_name"');
  });

  test('Playwright 코드를 .spec.ts 파일로 다운로드한다', async ({ qa, page }) => {
    await qa.generateFromSample('cart');
    await qa.openResultTab('playwright');

    const downloadPromise = page.waitForEvent('download');
    await page.getByTestId('download-playwright').click();
    const download = await downloadPromise;

    expect(download.suggestedFilename()).toBe('generated.spec.ts');
    const content = readFileSync(await download.path(), 'utf-8');
    expect(content).toContain('test.describe(');
  });

  test('리포트를 클립보드에 복사한다', async ({ qa, page, context }) => {
    await context.grantPermissions(['clipboard-read', 'clipboard-write']);
    await qa.generateFromSample('login');
    await qa.openResultTab('report');

    await page.getByTestId('copy-report').click();
    await expect(qa.toast).toHaveText('클립보드에 복사했습니다.');
    const copied = await page.evaluate(() => navigator.clipboard.readText());
    expect(copied).toContain('# QA Validation Report');
  });

  test('Ctrl+Enter로 실행할 수 있다', async ({ qa }) => {
    await qa.requirementInput.fill('장바구니에 상품을 담는다');
    await qa.requirementInput.press('Control+Enter');
    await expect(qa.verdict).toHaveText('PASS');
  });

  test('빈 요구사항은 요청을 보내지 않고 안내한다', async ({ qa, page }) => {
    let requested = false;
    page.on('request', (req) => { if (req.url().includes('/api/pipeline')) requested = true; });

    await qa.requirementInput.fill('   ');
    await qa.runButton.click();

    await expect(qa.errorMessage).toHaveText('요구사항을 입력하세요.');
    expect(requested).toBe(false);
  });

  test('API 키 없이 live 모드를 고르면 서버 오류 메시지를 보여준다', async ({ qa }) => {
    await qa.sample('login').click();
    await qa.modeSelect.selectOption('live');
    await qa.runButton.click();

    await expect(qa.errorMessage).toContainText('ANTHROPIC_API_KEY');
    await expect(qa.runButton).toBeEnabled();
  });
});
