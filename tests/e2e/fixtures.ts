import { readFileSync } from 'fs';
import { join } from 'path';
import { test as base } from '@playwright/test';
import { QaAgentPage } from './pages/QaAgentPage';

const SAMPLE_OUTPUT_DIR = join(__dirname, '..', '..', 'sample_outputs');

export function loadSampleTestCase(fileName: string): Record<string, unknown> {
  return JSON.parse(readFileSync(join(SAMPLE_OUTPUT_DIR, fileName), 'utf-8'));
}

export const test = base.extend<{ qa: QaAgentPage }>({
  qa: async ({ page }, use) => {
    const qa = new QaAgentPage(page);
    await qa.goto();
    await use(qa);
  },
});

export { expect } from '@playwright/test';
