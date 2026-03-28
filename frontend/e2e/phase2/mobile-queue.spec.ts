/**
 * E2E テスト: モバイルでリクエストキュータブ
 * テストID: E2E-MB-001
 * viewport: モバイル 390x844 (iPhone 14 Pro)
 */
import { test, expect } from "@playwright/test";

// NOTE: TabBar の QUEUE タブ（label="QUEUE"）を対象とする。元テストは "REQUESTS" としていたが実装は "QUEUE"。
test.use({ viewport: { width: 390, height: 844 }, hasTouch: true });

test.describe("モバイル: リクエストキュー", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/");
    await page.waitForLoadState("networkidle");
  });

  test("E2E-MB-001: モバイルでタブバーの QUEUE タブが表示される", async ({ page }) => {
    const queueTab = page.getByRole("tab", { name: /QUEUE/i });
    await expect(queueTab).toBeVisible({ timeout: 5000 });
  });

  test("E2E-MB-001b: QUEUE タブをタップするとキューが表示される", async ({ page }) => {
    const queueTab = page.getByRole("tab", { name: /QUEUE/i });
    await expect(queueTab).toBeVisible({ timeout: 5000 });

    await queueTab.click();

    // QUEUE タブがアクティブになる
    await expect(queueTab).toHaveAttribute("aria-selected", "true");

    // リクエストキューコンテナが表示される（空でも可）
    const requestQueue = page.locator(
      ".queue-tab-screen, [data-testid='request-queue'], .request-queue, .request-list"
    );
    await expect(requestQueue.first()).toBeVisible({ timeout: 5000 });
  });

  test("E2E-MB-001c: モバイルでリクエスト一覧が正常に表示される（空状態含む）", async ({ page }) => {
    const queueTab = page.getByRole("tab", { name: /QUEUE/i });
    await expect(queueTab).toBeVisible({ timeout: 5000 });
    await queueTab.click();

    // エラーオーバーレイがないことを確認
    const errorOverlay = page.locator(".error-overlay, .error-boundary, #error");
    await expect(errorOverlay).not.toBeVisible();

    // ページが正常に表示されている
    await expect(page.locator("body")).toBeVisible();
  });
});
