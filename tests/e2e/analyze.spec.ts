import { test, expect, loadSampleTestCase } from './fixtures';

test.describe('TC JSON 직접 검증', () => {

  test('traceability 중복이 있으면 FAIL과 8번 규칙 실패를 보여준다', async ({ qa }) => {
    const tc = loadSampleTestCase('invalid_duplicate_traceability_test_case.json');
    await qa.analyzeJson(JSON.stringify(tc));

    await expect(qa.verdict).toHaveText('FAIL');
    await expect(qa.ruleRow(8)).toHaveAttribute('data-passed', 'false');
    await expect(qa.metric('rules')).toHaveText('10/11');
    await expect(qa.page.getByTestId('result-mode')).toHaveText('직접 입력');
  });

  test('필수 필드가 없으면 Schema 오류가 목록으로 표시된다', async ({ qa }) => {
    const tc = loadSampleTestCase('login_test_case.json');
    delete tc.feature_name;
    await qa.analyzeJson(JSON.stringify(tc));

    await expect(qa.verdict).toHaveText('FAIL');
    await expect(qa.ruleRow(1)).toHaveAttribute('data-passed', 'false');
    await expect(qa.schemaResult).toContainText("'feature_name' is a required property");
  });

  test('JSON 문법 오류는 서버 요청 없이 안내한다', async ({ qa, page }) => {
    let requested = false;
    page.on('request', (req) => { if (req.url().includes('/api/analyze')) requested = true; });

    await qa.analyzeJson('{ "feature_name": ');

    await expect(qa.errorMessage).toContainText('JSON 형식이 올바르지 않습니다');
    expect(requested).toBe(false);
  });

  test('객체가 아닌 JSON(배열)은 거부한다', async ({ qa }) => {
    await qa.analyzeJson('[1, 2, 3]');
    await expect(qa.errorMessage).toHaveText('테스트 케이스는 JSON 객체({ ... })여야 합니다.');
  });

  test('입력값의 HTML은 실행되지 않고 글자로만 표시된다 (XSS)', async ({ qa, page }) => {
    const payload = '<img src=x onerror="window.__xss=1">';
    const tc = loadSampleTestCase('login_test_case.json');
    tc.feature_name = payload;
    tc.test_steps = [payload, '두 번째 단계'];
    await qa.analyzeJson(JSON.stringify(tc));

    await expect(qa.featureName).toHaveText(payload);
    await qa.openResultTab('testcase');
    await expect(page.getByTestId('tc-test_steps')).toContainText(payload);
    expect(await page.locator('[data-testid="result"] img').count()).toBe(0);
    expect(await page.evaluate(() => (window as unknown as { __xss?: number }).__xss)).toBeUndefined();
  });
});
