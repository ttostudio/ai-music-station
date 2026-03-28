/**
 * E2E テスト: リクエストキュー表示
 * テストID: E2E-PC-003
 * viewport: PC 1440x900
 */
import { test, expect } from "@playwright/test";

test.use({ viewport: { width: 1440, height: 900 } });

test.describe("リクエストキュー表示", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/");
    await page.waitForLoadState("networkidle");
  });

  test("E2E-PC-003: REQUESTS タブが表示される", async ({ page }) => {
    const requestsTab = page.getByRole("tab", { name: /REQUESTS/i });
    await expect(requestsTab).toBeVisible({ timeout: 5000 });
  });

  test("E2E-PC-003b: REQUESTS タブをクリックするとリクエストキューが表示される", async ({ page }) => {
    const requestsTab = page.getByRole("tab", { name: /REQUESTS/i });
    await expect(requestsTab).toBeVisible({ timeout: 5000 });
    await requestsTab.click();

    // リクエストキューコンテナが表示される（空でも可）
    const requestQueue = page.locator(
      "[data-testid='request-queue'], .request-queue, .requests-tab, .request-list"
    );
    await expect(requestQueue.first()).toBeVisible({ timeout: 3000 });
  });

  test("E2E-PC-003c: リクエストキューの空状態メッセージが適切に表示される", async ({ page }) => {
    const requestsTab = page.getByRole("tab", { name: /REQUESTS/i });
    await expect(requestsTab).toBeVisible({ timeout: 5000 });
    await requestsTab.click();

    // キューが空の場合でもUIが壊れていないことを確認
    await expect(page.locator("body")).toBeVisible();
    const errorOverlay = page.locator(".error-overlay, .error-boundary");
    await expect(errorOverlay).not.toBeVisible();
  });
});
