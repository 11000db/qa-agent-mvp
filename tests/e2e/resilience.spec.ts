import { test, expect } from './fixtures';
import { QaAgentPage } from './pages/QaAgentPage';

// page.route로 서버 응답을 바꿔서 실제로 만들기 어려운 장애 상황을 재현한다
test.describe('장애 / 예외 상황', () => {

  test('서버가 502를 주면 오류 메시지를 보여주고 다시 실행할 수 있다', async ({ qa, page }) => {
    await page.route('**/api/pipeline', (route) => route.fulfill({
      status: 502,
      contentType: 'application/json',
      body: JSON.stringify({ detail: 'Claude API 호출 실패: overloaded' }),
    }));

    await qa.sample('login').click();
    await qa.runButton.click();

    await expect(qa.errorMessage).toHaveText('Claude API 호출 실패: overloaded');
    await expect(qa.runButton).toBeEnabled();
    await expect(qa.emptyState).toBeVisible();
  });

  test('실패해도 직전 성공 결과는 유지된다', async ({ qa, page }) => {
    await qa.generateFromSample('login');

    await page.route('**/api/pipeline', (route) => route.fulfill({ status: 500, body: 'Internal Server Error' }));
    await qa.runButton.click();

    await expect(qa.errorMessage).toHaveText('요청 실패 (HTTP 500)');
    await expect(qa.result).toBeVisible();
    await expect(qa.verdict).toHaveText('PASS');
  });

  test('응답을 기다리는 동안 로딩을 표시하고 중복 실행을 막는다', async ({ qa, page }) => {
    let release!: () => void;
    const gate = new Promise<void>((resolve) => { release = resolve; });
    let calls = 0;
    await page.route('**/api/pipeline', async (route) => {
      calls += 1;
      await gate;
      await route.continue();
    });

    await qa.sample('login').click();
    await qa.runButton.click();

    await expect(qa.loading).toBeVisible();
    await expect(qa.runButton).toBeDisabled();
    await qa.requirementInput.press('Control+Enter');

    release();
    await expect(qa.verdict).toHaveText('PASS');
    await expect(qa.loading).toBeHidden();
    expect(calls).toBe(1);
  });

  test('서버에 연결할 수 없으면 상태 칩에 표시한다', async ({ page }) => {
    await page.route('**/api/health', (route) => route.abort('connectionrefused'));
    const qa = new QaAgentPage(page);
    await qa.goto();

    await expect(qa.serverStatus).toHaveAttribute('data-state', 'down');
    await expect(qa.serverStatus).toHaveText('서버 연결 실패');
  });

  test('422 검증 오류는 필드 이름과 함께 보여준다', async ({ qa, page }) => {
    await page.route('**/api/pipeline', (route) => route.fulfill({
      status: 422,
      contentType: 'application/json',
      body: JSON.stringify({ detail: [{ loc: ['body', 'requirement_text'], msg: 'String should have at most 20000 characters' }] }),
    }));

    await qa.requirementInput.fill('로그인');
    await qa.runButton.click();

    await expect(qa.errorMessage).toHaveText('입력값 오류: requirement_text - String should have at most 20000 characters');
  });
});
