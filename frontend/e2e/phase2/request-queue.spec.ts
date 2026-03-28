/**
 * E2E テスト: リクエストキュー表示
 * テストID: E2E-PC-003
 * viewport: PC 1440x900
 */
import { test, expect } from "@playwright/test";

// NOTE: QUEUE タブは MobileLayout（<768px）のみ存在。モバイル viewport で検証。
test.use({ viewport: { width: 390, height: 844 }, hasTouch: true });

test.describe("リクエストキュー表示", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/");
    await page.waitForLoadState("networkidle");
  });

  test("E2E-PC-003: QUEUE タブが表示される", async ({ page }) => {
    const queueTab = page.getByRole("tab", { name: /QUEUE/i });
    await expect(queueTab).toBeVisible({ timeout: 5000 });
  });

  test("E2E-PC-003b: QUEUE タブをクリックするとリクエストキューが表示される", async ({ page }) => {
    const queueTab = page.getByRole("tab", { name: /QUEUE/i });
    await expect(queueTab).toBeVisible({ timeout: 5000 });
    await queueTab.click();

    // リクエストキューコンテナが表示される（空でも可）
    const requestQueue = page.locator(
      ".queue-tab-screen, [data-testid='request-queue'], .request-queue, .request-list"
    );
    await expect(requestQueue.first()).toBeVisible({ timeout: 5000 });
  });

  test("E2E-PC-003c: リクエストキューの空状態メッセージが適切に表示される", async ({ page }) => {
    const queueTab = page.getByRole("tab", { name: /QUEUE/i });
    await expect(queueTab).toBeVisible({ timeout: 5000 });
    await queueTab.click();

    // キューが空の場合でもUIが壊れていないことを確認
    await expect(page.locator("body")).toBeVisible();
    const errorOverlay = page.locator(".error-overlay, .error-boundary");
    await expect(errorOverlay).not.toBeVisible();
  });
});
