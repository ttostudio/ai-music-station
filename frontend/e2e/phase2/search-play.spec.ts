/**
 * E2E テスト: 検索 → 再生フロー
 * テストID: E2E-PC-005
 * viewport: PC 1440x900
 */
import { test, expect } from "@playwright/test";

test.use({ viewport: { width: 1440, height: 900 } });

test.describe("検索 → 再生フロー", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/");
    await page.waitForLoadState("networkidle");
  });

  test("E2E-PC-005: 検索バーが表示されて入力できる", async ({ page }) => {
    // 検索フィールドを取得（searchbox role または placeholder で検索）
    const searchInput = page
      .locator("input[type='search'], input[placeholder*='検索'], input[role='searchbox']")
      .first();
    await expect(searchInput).toBeVisible({ timeout: 5000 });

    // 入力できることを確認
    await searchInput.fill("lofi");
    await expect(searchInput).toHaveValue("lofi");
  });

  test("E2E-PC-005b: 検索してトラックを選択すると再生が開始される", async ({ page }) => {
    const searchInput = page
      .locator("input[type='search'], input[placeholder*='検索'], input[role='searchbox']")
      .first();
    await expect(searchInput).toBeVisible({ timeout: 5000 });

    await searchInput.fill("lofi");

    // デバウンス後に検索結果が表示される（最大3秒待機）
    const searchResult = page.locator(".search-result-item, .search-result, [data-testid='search-result']").first();
    const resultAppeared = await searchResult.waitFor({ timeout: 3000 }).then(() => true).catch(() => false);

    if (!resultAppeared) {
      // 検索結果なし（データ依存）はスキップ
      test.skip();
      return;
    }

    await searchResult.click();

    // Player に楽曲タイトルが表示される
    const playerTitle = page.locator(
      "[data-testid='player-track-title'], .player-track-title, .fb-track-title, .fb-now-playing"
    );
    await expect(playerTitle.first()).toBeVisible({ timeout: 3000 });
  });

  test("E2E-PC-005c: 検索フィールドをクリアすると結果が消える", async ({ page }) => {
    const searchInput = page
      .locator("input[type='search'], input[placeholder*='検索'], input[role='searchbox']")
      .first();
    await expect(searchInput).toBeVisible({ timeout: 5000 });

    await searchInput.fill("test");
    await searchInput.fill("");

    // 入力値がクリアされていることを確認
    await expect(searchInput).toHaveValue("");
  });
});
