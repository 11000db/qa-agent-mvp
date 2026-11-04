// TC v1 (Day 24 이전): git show 10acc79~1:sample_outputs/cart_test_case.json
// 절차 변환
// - 상품 PROD-001(재고 100) → PRD-001
// - "수량 3개로 설정 후 담기" → 데모 앱은 1개씩 담기라 담기를 반복
// - E1 "재고 50개 상품에 100개" → 재고 5개 상품(PRD-002)에 6개
import { test, expect, Shop, PRODUCT, PRICE, excluded, won } from '../shop';

const P = PRODUCT.normal;

async function addTimes(shop: Shop, productId: string, times: number) {
  for (let i = 0; i < times; i++) await shop.addToCart(productId);
}

test.describe('장바구니 v1 - 정상 흐름', () => {
  test("[ER1] 담기 클릭 시 '장바구니에 추가되었습니다' 메시지가 표시된다", { tag: '@happy' }, async ({ page }) => {
    await new Shop(page).addToCart(P);
    await expect(page.getByText('장바구니에 추가되었습니다')).toBeVisible();
  });

  test('[ER2] 장바구니에 상품명, 가격, 수량, 소계가 정확히 표시된다', { tag: '@happy' }, async ({ page }) => {
    const shop = new Shop(page);
    await addTimes(shop, P, 3);
    await shop.openCart();
    await expect(shop.row(P)).toContainText('테스트 상품 A');
    await expect(shop.row(P)).toContainText(won(PRICE[P]));
    await shop.expectQuantity(P, 3);
    await expect(shop.row(P).locator('.subtotal')).toHaveText(won(PRICE[P] * 3));
  });

  test('[ER3] 같은 상품을 다시 담으면 새 항목 없이 수량만 증가한다 (3+2=5)', { tag: '@happy' }, async ({ page }) => {
    const shop = new Shop(page);
    await addTimes(shop, P, 3);
    await addTimes(shop, P, 2);
    await shop.openCart();
    await expect(shop.rows()).toHaveCount(1);
    await shop.expectQuantity(P, 5);
  });

  test('[ER4] 수량을 7로 바꾸면 UI가 업데이트되고 총 금액이 재계산된다', { tag: '@happy' }, async ({ page }) => {
    const shop = new Shop(page);
    await addTimes(shop, P, 5);
    await shop.openCart();
    await shop.setQuantity(P, '7');
    await shop.expectQuantity(P, 7);
    await expect(shop.total()).toContainText(won(PRICE[P] * 7));
  });

  test("[ER5] 삭제 후 장바구니 카운트가 0이 되고 '장바구니가 비어있습니다'가 표시된다", { tag: '@happy' }, async ({ page }) => {
    const shop = new Shop(page);
    await shop.addToCart(P);
    await shop.openCart();
    await shop.remove(P);
    await expect(shop.cartBadge()).toHaveText('장바구니 (0)');
    await expect(page.getByText(/장바구니가 비어 ?있습니다/)).toBeVisible();
  });

  test('[ER6] 모든 변경 사항이 새로고침 후에도 유지된다', { tag: '@happy' }, async ({ page }) => {
    const shop = new Shop(page);
    await addTimes(shop, P, 2);
    await shop.openCart();
    await shop.setQuantity(P, '7');
    await page.reload();
    await shop.expectQuantity(P, 7);
  });
});

test.describe('장바구니 v1 - Negative', () => {
  test("[N1] 품절 상품을 담으면 '품절된 상품입니다' 경고가 표시되고 추가되지 않는다", async ({ page }) => {
    const shop = new Shop(page);
    await shop.addToCart(PRODUCT.soldOut);
    await expect(page.getByText('품절된 상품입니다')).toBeVisible();
    await shop.openCart();
    await expect(shop.row(PRODUCT.soldOut)).toHaveCount(0);
  });

  test('[N2] 수량 -5를 입력하면 에러 메시지가 표시되고 변경이 차단된다', async ({ page }) => {
    const shop = new Shop(page);
    await shop.addToCart(P);
    await shop.openCart();
    await shop.setQuantity(P, '-5');
    await expect(page.getByText(/올바른 수량|1 이상/)).toBeVisible();
    await shop.expectQuantity(P, 1);
  });

  test("[N3] 수량에 'abc'를 입력하면 에러 메시지가 표시된다", async ({ page }) => {
    const shop = new Shop(page);
    await shop.addToCart(P);
    await shop.openCart();
    await shop.setQuantity(P, 'abc');
    await expect(page.getByText(/올바른 (수량|숫자)/)).toBeVisible();
  });

  test('[N4] 비로그인 상태에서 담기를 시도하면 로그인 페이지로 이동한다', async ({ page }) => {
    await new Shop(page).addToCart(P);
    await expect(page).toHaveURL(/\/login/);
  });

  excluded('out-of-scope', 'N5', '네트워크 오류 시 "일시적인 오류" 메시지가 표시된다', '요구사항에 없는 클라이언트 네트워크 처리');

  test('[N6] 수량을 0으로 바꾸면 삭제 처리되거나 최소 수량 1로 제한된다', async ({ page }) => {
    page.on('dialog', (d) => d.accept());
    const shop = new Shop(page);
    await shop.addToCart(P);
    await shop.openCart();
    await shop.setQuantity(P, '0');
    // 삭제되었거나(행 없음), 남아 있다면 수량이 0이 아니어야 한다
    if (await shop.row(P).count() > 0) {
      await expect(shop.row(P).getByLabel('수량')).not.toHaveValue('0');
    }
  });
});

test.describe('장바구니 v1 - Edge', () => {
  test('[E1] 재고보다 많은 수량을 입력하면 재고 한도 메시지와 함께 제한된다', async ({ page }) => {
    const shop = new Shop(page);
    await shop.addToCart(PRODUCT.lowStock);
    await shop.openCart();
    await shop.setQuantity(PRODUCT.lowStock, '6');
    await expect(page.getByText(/재고/)).toBeVisible();
    await expect(shop.row(PRODUCT.lowStock).getByLabel('수량')).not.toHaveValue('6');
  });

  test('[E2] 999999999처럼 큰 수를 입력하면 최대 수량 제한 메시지가 표시된다', async ({ page }) => {
    const shop = new Shop(page);
    await shop.addToCart(P);
    await shop.openCart();
    await shop.setQuantity(P, '999999999');
    await expect(page.getByText(/최대/)).toBeVisible();
  });

  excluded('out-of-scope', 'E3', '장바구니 최대 100개 상품 제한 경고', '요구사항에 장바구니 상품 수 제한 없음');
  excluded('not-automatable', 'E4', '여러 탭에서 동시에 담아도 수량이 정확하다', '동시 요청 순서를 브라우저 테스트로 통제할 수 없음');
  excluded('out-of-scope', 'E5', '수정 중 세션이 만료되면 로그인 페이지로 이동한다', '요구사항에 세션 만료 정책 없음');
  excluded('out-of-scope', 'E6', '소수점 가격의 총액 계산이 정확하다', '데모 앱 가격은 정수');
  excluded('out-of-scope', 'E7', '판매 종료 상품은 안내와 함께 회색 처리된다', '요구사항에 판매 종료 상태 없음');
});
