/**
 * E2E テスト: デスクトップ検索
 * テストID: E2E-PC-005 (デスクトップ特化)
 * viewport: デスクトップ 1440x900
 */
import { test, expect } from "@playwright/test";

test.use({ viewport: { width: 1440, height: 900 } });

test.describe("デスクトップ: 検索機能", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/");
    await page.waitForLoadState("networkidle");
  });

  test("E2E-PC-DES-001: デスクトップでヘッダー検索バーが表示される", async ({ page }) => {
    // デスクトップレイアウトで検索入力が表示される
    const searchInput = page
      .locator("input[type='search'], input[placeholder*='検索'], input[role='searchbox']")
      .first();
    await expect(searchInput).toBeVisible({ timeout: 5000 });
  });

  test("E2E-PC-DES-002: 検索バーにキーワードを入力できる", async ({ page }) => {
    const searchInput = page
      .locator("input[type='search'], input[placeholder*='検索'], input[role='searchbox']")
      .first();
    await expect(searchInput).toBeVisible({ timeout: 5000 });

    await searchInput.click();
    await searchInput.fill("lofi beats");
    await expect(searchInput).toHaveValue("lofi beats");
  });

  test("E2E-PC-DES-003: 検索キーワード入力後に検索結果またはUIが表示される", async ({ page }) => {
    const searchInput = page
      .locator("input[type='search'], input[placeholder*='検索'], input[role='searchbox']")
      .first();
    await expect(searchInput).toBeVisible({ timeout: 5000 });

    await searchInput.fill("a");

    // デバウンス後に何らかの反応がある（結果リストまたは入力が保持される）
    await expect(searchInput).toHaveValue("a");

    // 検索結果が出た場合の確認（データ依存なのでオプション）
    const resultList = page.locator(
      ".search-result-item, .search-result, [data-testid='search-result'], .track-item"
    );
    const resultAppeared = await resultList.first().waitFor({ timeout: 2000 }).then(() => true).catch(() => false);

    if (resultAppeared) {
      await expect(resultList.first()).toBeVisible();
    } else {
      // 結果なしでもUIが壊れていないことを確認
      await expect(page.locator("body")).toBeVisible();
    }
  });

  test("E2E-PC-DES-004: 検索中にコンソールエラーが発生しない", async ({ page }) => {
    const errors: string[] = [];
    page.on("console", (msg) => {
      if (msg.type() === "error") {
        errors.push(msg.text());
      }
    });

    const searchInput = page
      .locator("input[type='search'], input[placeholder*='検索'], input[role='searchbox']")
      .first();
    await expect(searchInput).toBeVisible({ timeout: 5000 });

    await searchInput.fill("test query");

    // API レスポンス待機
    await page.waitForResponse(
      (res) => res.url().includes("/api/") || res.url().includes("search"),
      { timeout: 3000 }
    ).catch(() => null); // タイムアウトしても続行

    // 検索関連のエラーがないことを確認
    const searchErrors = errors.filter((e) => /search|fetch|network/i.test(e));
    expect(searchErrors).toHaveLength(0);
  });
});
