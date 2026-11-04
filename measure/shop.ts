import { test, expect, type Locator, type Page } from '@playwright/test';

/** 시드 계정 (TC의 사전 조건 "테스트 계정이 등록되어 있어야 한다"에 해당) */
export const ACCOUNT_V2 = { email: 'test@example.com', password: 'Test1234!', name: '테스트' };
export const ACCOUNT_V1 = { email: 'testuser@example.com', password: 'Test1234!@', name: '테스트유저' };
export const DUPLICATE_EMAIL_V2 = 'duplicate@example.com';
export const DUPLICATE_EMAIL_V1 = 'test@example.com';

/** TC의 상품 ID를 데모 앱 상품에 대응 */
export const PRODUCT = { normal: 'PRD-001', lowStock: 'PRD-002', soldOut: 'PRD-003' };
export const PRICE = { 'PRD-001': 10000, 'PRD-002': 25000, 'PRD-003': 15000 } as const;

export type ExcludedKind = 'not-automatable' | 'out-of-scope' | 'no-criteria';

/** 자동화하지 않는 TC 항목: 사유와 함께 기록만 한다 */
export function excluded(kind: ExcludedKind, id: string, text: string, reason: string) {
  test(`[${id}] ${text}`, { tag: `@${kind}`, annotation: { type: kind, description: reason } }, () => {
    test.skip(true, reason);
  });
}

export function uniqueEmail(prefix = 'user'): string {
  return `${prefix}.${Date.now()}.${Math.random().toString(36).slice(2, 8)}@example.com`;
}

export function won(amount: number): string {
  return `${amount.toLocaleString('ko-KR')}원`;
}

export class Shop {
  constructor(readonly page: Page) {}

  /**
   * 폼 제출 후 새 페이지가 열릴 때까지 기다린다.
   * 기다리지 않으면 이전 페이지를 보고 판정해서, 결함이 있어도 테스트가 통과하는 경우가 생긴다.
   */
  async submit(button: Locator) {
    const navigated = this.page.waitForEvent('framenavigated', (frame) => frame === this.page.mainFrame());
    await button.click();
    await navigated;
    await this.page.waitForLoadState();
  }

  // ---- 로그인 ----
  emailInput() { return this.page.getByLabel('이메일', { exact: true }); }
  passwordInput() { return this.page.getByLabel('비밀번호', { exact: true }); }
  nameInput() { return this.page.getByLabel('이름', { exact: true }); }

  async login(email: string, password: string) {
    await this.page.goto('/shop/login');
    await this.emailInput().fill(email);
    await this.passwordInput().fill(password);
    await this.submit(this.page.getByRole('button', { name: '로그인', exact: true }));
  }

  async logout() {
    await this.submit(this.page.getByRole('button', { name: '로그아웃' }));
  }

  async expectLoggedIn() {
    await expect(this.page.getByRole('button', { name: '로그아웃' })).toBeVisible();
  }

  async expectLoggedOut() {
    await expect(this.page.getByRole('link', { name: '로그인', exact: true })).toBeVisible();
    await expect(this.page.getByRole('button', { name: '로그아웃' })).toHaveCount(0);
  }

  // ---- 회원가입 ----
  async signup(name: string, email: string, password: string) {
    await this.page.goto('/shop/signup');
    await this.nameInput().fill(name);
    await this.emailInput().fill(email);
    await this.passwordInput().fill(password);
    await this.submit(this.page.getByRole('button', { name: '회원가입', exact: true }));
  }

  async expectSignupSucceeded() {
    await expect(this.page.getByText(/회원가입이 완료되었습니다|환영합니다/)).toBeVisible();
  }

  async expectSignupBlocked() {
    await expect(this.page.getByRole('button', { name: '회원가입', exact: true })).toBeVisible();
    await expect(this.page.getByText(/회원가입이 완료되었습니다|환영합니다/)).toHaveCount(0);
  }

  // ---- 장바구니 ----
  async addToCart(productId: string) {
    await this.page.goto(`/shop/products/${productId}`);
    await this.submit(this.page.getByRole('button', { name: '장바구니 담기' }));
  }

  async openCart() {
    await this.page.goto('/shop/cart');
  }

  rows() { return this.page.locator('tbody tr'); }
  row(productId: string) { return this.page.locator(`tbody tr[data-product="${productId}"]`); }
  cartBadge() { return this.page.getByRole('link', { name: /^장바구니 \(\d+\)$/ }); }
  total() { return this.page.locator('.total'); }

  async setQuantity(productId: string, value: string) {
    const row = this.row(productId).first();
    await row.getByLabel('수량').fill(value);
    await this.submit(row.getByRole('button', { name: '변경' }));
  }

  async remove(productId: string) {
    await this.submit(this.row(productId).first().getByRole('button', { name: '삭제' }));
  }

  async expectQuantity(productId: string, qty: number) {
    await expect(this.row(productId).first().getByLabel('수량')).toHaveValue(String(qty));
  }
}

export { test, expect };
