// TC v2 (Day 24 이후): sample_outputs/cart_test_case.json
// 사전 조건의 상품 PRD-001(재고 100), PRD-002(재고 5), PRD-003(품절)은 데모 앱에 같은 ID로 있다
import { test, expect, Shop, PRODUCT, PRICE, excluded, won } from '../shop';

const P = PRODUCT.normal;

test.describe('장바구니 v2 - 정상 흐름', () => {
  test('[ER1] 담기 클릭 시 추가 메시지가 표시되고 장바구니 배지가 1 증가한다', { tag: '@happy' }, async ({ page }) => {
    const shop = new Shop(page);
    await shop.addToCart(P);
    await expect(page.getByText('장바구니에 추가되었습니다')).toBeVisible();
    await expect(shop.cartBadge()).toHaveText('장바구니 (1)');
  });

  test('[ER2] 장바구니에 상품명, 가격, 수량 1개가 표시된다', { tag: '@happy' }, async ({ page }) => {
    const shop = new Shop(page);
    await shop.addToCart(P);
    await shop.openCart();
    await expect(shop.row(P)).toContainText('테스트 상품 A');
    await expect(shop.row(P)).toContainText(won(PRICE[P]));
    await shop.expectQuantity(P, 1);
  });

  test('[ER3] 같은 상품을 다시 담으면 새 항목 없이 수량이 2개가 된다', { tag: '@happy' }, async ({ page }) => {
    const shop = new Shop(page);
    await shop.addToCart(P);
    await shop.addToCart(P);
    await shop.openCart();
    await expect(shop.rows()).toHaveCount(1);
    await shop.expectQuantity(P, 2);
  });

  test('[ER4] 수량을 5로 바꾸면 수량 5와 총 금액(단가×5)이 반영된다', { tag: '@happy' }, async ({ page }) => {
    const shop = new Shop(page);
    await shop.addToCart(P);
    await shop.addToCart(P);
    await shop.openCart();
    await shop.setQuantity(P, '5');
    await shop.expectQuantity(P, 5);
    await expect(shop.total()).toContainText(won(PRICE[P] * 5), { timeout: 2000 });
  });

  test('[ER5] 삭제 버튼을 누르면 상품이 목록에서 제거된다', { tag: '@happy' }, async ({ page }) => {
    const shop = new Shop(page);
    await shop.addToCart(P);
    await shop.openCart();
    await shop.remove(P);
    await expect(shop.row(P)).toHaveCount(0);
  });

  test('[ER6] 장바구니가 비면 빈 상태 메시지와 쇼핑 계속하기 버튼이 표시된다', { tag: '@happy' }, async ({ page }) => {
    const shop = new Shop(page);
    await shop.addToCart(P);
    await shop.openCart();
    await shop.remove(P);
    await expect(page.getByText(/장바구니가 비어 ?있습니다/)).toBeVisible();
    await expect(page.getByRole('link', { name: '쇼핑 계속하기' })).toBeVisible();
  });

  test('[ER7] 장바구니 변경 사항은 새로고침 후에도 유지된다', { tag: '@happy' }, async ({ page }) => {
    const shop = new Shop(page);
    await shop.addToCart(P);
    await shop.openCart();
    await shop.setQuantity(P, '3');
    await page.reload();
    await shop.expectQuantity(P, 3);
  });
});

test.describe('장바구니 v2 - Negative', () => {
  test('[N1] 품절 상품(PRD-003)은 품절 메시지가 표시되고 담기지 않는다', async ({ page }) => {
    const shop = new Shop(page);
    await shop.addToCart(PRODUCT.soldOut);
    await expect(page.getByText(/품절/).filter({ hasText: /상품입니다/ })).toBeVisible();
    await shop.openCart();
    await expect(shop.row(PRODUCT.soldOut)).toHaveCount(0);
  });

  test("[N2] 수량 0을 입력하면 '1개 이상 입력해주세요' 메시지 또는 삭제 확인 팝업이 표시된다", async ({ page }) => {
    let dialog = false;
    page.on('dialog', async (d) => { dialog = true; await d.accept(); });
    const shop = new Shop(page);
    await shop.addToCart(P);
    await shop.openCart();
    await shop.setQuantity(P, '0');
    if (!dialog) await expect(page.getByText(/1개 이상/)).toBeVisible();
  });

  test('[N3] 음수(-5)를 입력하면 차단되거나 오류 메시지가 표시된다', async ({ page }) => {
    const shop = new Shop(page);
    await shop.addToCart(P);
    await shop.openCart();
    await shop.setQuantity(P, '-5');
    await expect(page.getByText(/올바른 수량/)).toBeVisible();
    await shop.expectQuantity(P, 1);
  });

  test("[N4] 문자열('abc')을 입력하면 차단되거나 오류 메시지가 표시된다", async ({ page }) => {
    const shop = new Shop(page);
    await shop.addToCart(P);
    await shop.openCart();
    await shop.setQuantity(P, 'abc');
    await expect(page.getByText(/올바른 수량|숫자/)).toBeVisible();
  });

  test('[N5] 재고보다 많은 수량(150, 재고 100)은 재고 부족 메시지와 함께 거부된다', async ({ page }) => {
    const shop = new Shop(page);
    await shop.addToCart(P);
    await shop.openCart();
    await shop.setQuantity(P, '150');
    await expect(page.getByText(/재고가 부족합니다/)).toBeVisible();
    await shop.expectQuantity(P, 1);
  });

  test('[N6] 로그아웃 상태에서 담기를 누르면 로그인 페이지로 이동하거나 로그인 유도 메시지가 표시된다', async ({ page }) => {
    await new Shop(page).addToCart(P);
    await expect(page.getByText(/로그인이 필요|로그인 후/).or(page.getByRole('heading', { name: '로그인' }))).toBeVisible();
  });

  excluded('not-automatable', 'N7', '여러 상품 수량 변경을 동시에 요청해도 데이터 정합성이 유지된다', '동시 요청 순서를 브라우저 테스트로 통제할 수 없음');
});

test.describe('장바구니 v2 - Edge', () => {
  excluded('out-of-scope', 'E1', '상품 100개를 담고 최대 수량으로 바꿔도 UI가 깨지지 않는다', '데모 앱 상품이 3개뿐');
  excluded('out-of-scope', 'E2', '수량 1에서 감소 버튼을 누르면 삭제 확인 또는 자동 삭제', '요구사항에 감소 버튼 없음');
  excluded('out-of-scope', 'E3', '수량 변경 중 네트워크가 끊겼다 복구되면 롤백 또는 재시도', '요구사항에 없는 클라이언트 네트워크 처리');
  excluded('not-automatable', 'E4', '다른 기기에서 수정한 장바구니가 동기화된다', '같은 계정의 다중 기기 장바구니가 요구사항에 없음');
  excluded('out-of-scope', 'E5', '담은 뒤 관리자가 품절 처리하면 장바구니에 품절 표시', '요구사항에 관리자 기능 없음');

  test('[E6][Regression] 상품을 담은 채 로그아웃 후 재로그인하면 장바구니가 유지된다', async ({ page }) => {
    const shop = new Shop(page);
    await shop.login('test@example.com', 'Test1234!');
    await shop.addToCart(P);
    await shop.logout();
    await shop.login('test@example.com', 'Test1234!');
    await shop.openCart();
    await shop.expectQuantity(P, 1);
  });

  test('[E7][Regression] 삭제 후 같은 상품을 다시 담으면 수량 1로 새로 추가된다', async ({ page }) => {
    const shop = new Shop(page);
    await shop.addToCart(P);
    await shop.addToCart(P);
    await shop.openCart();
    await shop.remove(P);
    await shop.addToCart(P);
    await shop.openCart();
    await shop.expectQuantity(P, 1);
  });

  test('[E8][Regression] 장바구니에서 상품명을 누르면 상세로 가고, 뒤로가기로 장바구니에 돌아온다', async ({ page }) => {
    const shop = new Shop(page);
    await shop.addToCart(P);
    await shop.openCart();
    await shop.row(P).getByRole('link', { name: '테스트 상품 A' }).click();
    await expect(page).toHaveURL(new RegExp(`/shop/products/${P}$`));
    await page.goBack();
    await expect(page).toHaveURL(/\/shop\/cart$/);
  });

  excluded('out-of-scope', 'E9', 'API 응답이 5초 이상 지연되면 로딩 표시와 타임아웃 처리', '서버 렌더링 앱이라 클라이언트 로딩 표시 없음');

  test('[E10] 재고 5개 상품(PRD-002)을 5개 담은 상태에서 6개로 바꾸면 재고 부족 오류가 난다', async ({ page }) => {
    const shop = new Shop(page);
    await shop.addToCart(PRODUCT.lowStock);
    await shop.openCart();
    await shop.setQuantity(PRODUCT.lowStock, '5');
    await shop.setQuantity(PRODUCT.lowStock, '6');
    await expect(page.getByText(/재고가 부족합니다/)).toBeVisible();
  });
});
