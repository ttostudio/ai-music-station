/**
 * E2E テスト: モバイルでリクエストキュータブ
 * テストID: E2E-MB-001
 * viewport: モバイル 390x844 (iPhone 14 Pro)
 */
import { test, expect } from "@playwright/test";

test.use({ viewport: { width: 390, height: 844 } });

test.describe("モバイル: リクエストキュー", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/");
    await page.waitForLoadState("networkidle");
  });

  test("E2E-MB-001: モバイルでタブバーの REQUESTS タブが表示される", async ({ page }) => {
    const requestsTab = page.getByRole("tab", { name: /REQUESTS/i });
    await expect(requestsTab).toBeVisible({ timeout: 5000 });
  });

  test("E2E-MB-001b: REQUESTS タブをタップするとキューが表示される", async ({ page }) => {
    const requestsTab = page.getByRole("tab", { name: /REQUESTS/i });
    await expect(requestsTab).toBeVisible({ timeout: 5000 });

    await requestsTab.tap();

    // REQUESTS タブがアクティブになる
    await expect(requestsTab).toHaveAttribute("aria-selected", "true");

    // リクエストキューコンテナが表示される（空でも可）
    const requestQueue = page.locator(
      "[data-testid='request-queue'], .request-queue, .requests-tab, .request-list"
    );
    await expect(requestQueue.first()).toBeVisible({ timeout: 3000 });
  });

  test("E2E-MB-001c: モバイルでリクエスト一覧が正常に表示される（空状態含む）", async ({ page }) => {
    const requestsTab = page.getByRole("tab", { name: /REQUESTS/i });
    await expect(requestsTab).toBeVisible({ timeout: 5000 });
    await requestsTab.tap();

    // エラーオーバーレイがないことを確認
    const errorOverlay = page.locator(".error-overlay, .error-boundary, #error");
    await expect(errorOverlay).not.toBeVisible();

    // ページが正常に表示されている
    await expect(page.locator("body")).toBeVisible();
  });
});
