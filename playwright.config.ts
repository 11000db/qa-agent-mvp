import { defineConfig, devices } from '@playwright/test';

const PORT = Number(process.env.E2E_PORT ?? 8123);
const BASE_URL = `http://127.0.0.1:${PORT}`;
const CI = !!process.env.CI;

// 로컬에 설치된 브라우저 버전이 다를 때만 경로를 지정한다 (CI는 npx playwright install 사용)
const executablePath = process.env.PW_CHROMIUM_PATH;

// 결함 검출률 측정: SHOP_FAULT=L1 처럼 지정하면 데모 쇼핑몰에 해당 결함이 켜진다
const faultHeaders = process.env.SHOP_FAULT ? { 'X-Shop-Fault': process.env.SHOP_FAULT } : undefined;

export default defineConfig({
  timeout: 30_000,
  expect: { timeout: 5_000 },
  fullyParallel: true,
  forbidOnly: CI,
  retries: CI ? 1 : 0,
  reporter: CI
    ? [['list'], ['html', { open: 'never' }], ['junit', { outputFile: 'test-results/e2e-junit.xml' }]]
    : [['list'], ['html', { open: 'never' }]],
  use: {
    baseURL: BASE_URL,
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    launchOptions: executablePath ? { executablePath } : {},
  },
  projects: [
    // 웹 UI E2E (자체 서버, mock 모드) - CI에서 실행
    { name: 'ui-desktop', testDir: './tests/e2e', use: { ...devices['Desktop Chrome'] } },
    { name: 'ui-mobile', testDir: './tests/e2e', use: { ...devices['Pixel 7'] } },
    // 파이프라인이 생성한 테스트 (외부 사이트 대상) - 수동 실행
    { name: 'generated', testDir: './playwright', use: { ...devices['Desktop Chrome'] } },
    // AI 생성 TC를 옮긴 측정용 테스트 (데모 쇼핑몰 /shop 대상) - measure/run_measurement.py가 실행
    { name: 'measure-v1', testDir: './measure/tc_v1', use: { ...devices['Desktop Chrome'], extraHTTPHeaders: faultHeaders } },
    { name: 'measure-v2', testDir: './measure/tc_v2', use: { ...devices['Desktop Chrome'], extraHTTPHeaders: faultHeaders } },
  ],
  webServer: {
    command: 'python app/server.py',
    url: `${BASE_URL}/api/health`,
    env: { PORT: String(PORT), HOST: '127.0.0.1', ANTHROPIC_API_KEY: '', SHOP_FAULT_INJECTION: '1' },
    reuseExistingServer: !CI,
    timeout: 30_000,
  },
});
