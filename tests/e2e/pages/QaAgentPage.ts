import { expect, type Locator, type Page } from '@playwright/test';

export type ResultTab = 'validation' | 'testcase' | 'report' | 'playwright' | 'json';

/** QA Agent 웹 UI Page Object */
export class QaAgentPage {
  readonly page: Page;
  readonly serverStatus: Locator;
  readonly requirementInput: Locator;
  readonly charCount: Locator;
  readonly modeSelect: Locator;
  readonly runButton: Locator;
  readonly tcJsonInput: Locator;
  readonly analyzeButton: Locator;
  readonly errorMessage: Locator;
  readonly emptyState: Locator;
  readonly loading: Locator;
  readonly result: Locator;
  readonly verdict: Locator;
  readonly featureName: Locator;
  readonly ruleRows: Locator;
  readonly schemaResult: Locator;
  readonly toast: Locator;

  constructor(page: Page) {
    this.page = page;
    const id = (testId: string) => page.getByTestId(testId);
    this.serverStatus = id('server-status');
    this.requirementInput = id('requirement-input');
    this.charCount = id('char-count');
    this.modeSelect = id('mode-select');
    this.runButton = id('run-button');
    this.tcJsonInput = id('tc-json-input');
    this.analyzeButton = id('analyze-button');
    this.errorMessage = id('error-message');
    this.emptyState = id('empty-state');
    this.loading = id('loading');
    this.result = id('result');
    this.verdict = id('verdict');
    this.featureName = id('feature-name');
    this.ruleRows = id('rule-row');
    this.schemaResult = id('schema-result');
    this.toast = id('toast');
  }

  async goto() {
    await this.page.goto('/');
    await expect(this.serverStatus).not.toHaveAttribute('data-state', 'loading');
  }

  sample(name: string): Locator {
    return this.page.getByTestId(`sample-${name}`);
  }

  ruleRow(no: number): Locator {
    return this.page.locator(`[data-testid="rule-row"][data-rule="${no}"]`);
  }

  metric(name: 'rules' | 'schema' | 'negative' | 'edge' | 'regression'): Locator {
    return this.page.getByTestId(`metric-${name}`);
  }

  output(kind: 'report' | 'playwright' | 'json'): Locator {
    return this.page.getByTestId(`${kind}-output`);
  }

  async generateFromSample(name: string) {
    await this.sample(name).click();
    await this.runButton.click();
    await expect(this.result).toBeVisible();
  }

  async switchInputToAnalyze() {
    await this.page.getByTestId('input-tab-analyze').click();
  }

  async analyzeJson(json: string) {
    await this.switchInputToAnalyze();
    await this.tcJsonInput.fill(json);
    await this.analyzeButton.click();
  }

  async openResultTab(tab: ResultTab) {
    await this.page.getByTestId(`result-tab-${tab}`).click();
  }
}
