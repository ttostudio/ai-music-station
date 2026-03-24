/**
 * E2E テスト: PC フロー
 * テスト仕様書 シナリオ P-01 〜 P-04 に対応
 * viewport: 1440x900
 */
import { test, expect } from "@playwright/test";

test.use({
  viewport: { width: 1440, height: 900 },
});

test.beforeEach(async ({ page }) => {
  await page.goto("/");
  await page.waitForLoadState("networkidle");
});

test("P-01: PC レイアウト → フローティングバーが表示される", async ({ page }) => {
  await expect(page.locator(".floating-bar")).toBeVisible({ timeout: 5000 });
});

test("P-01: PC レイアウト → タブバーが表示されない", async ({ page }) => {
  await expect(page.locator(".tabbar-outer")).not.toBeVisible();
});

test("P-01: PC レイアウト → ビジュアライザー (canvas) が存在する", async ({ page }) => {
  await expect(page.locator("canvas")).toBeVisible({ timeout: 5000 });
});

test("P-02: チャンネルメニューボタンクリック → メニューが表示される", async ({ page }) => {
  const channelMenuBtn = page.getByRole("button", { name: "チャンネルメニュー" });
  await expect(channelMenuBtn).toBeVisible({ timeout: 5000 });
  await channelMenuBtn.click();
  // チャンネルメニューポップアップが表示される
  await expect(page.locator(".channel-menu")).toBeVisible({ timeout: 3000 });
});

test("P-02: チャンネルメニュー → チャンネルリストが表示される", async ({ page }) => {
  const channelMenuBtn = page.getByRole("button", { name: "チャンネルメニュー" });
  await channelMenuBtn.click();
  // チャンネルリストにアイテムが存在する
  const menuItems = page.locator(".channel-menu-item");
  await expect(menuItems.first()).toBeVisible({ timeout: 3000 });
});

test("P-03: 歌詞パネル表示トグル", async ({ page }) => {
  const lyricsBtn = page.getByRole("button", { name: "歌詞パネル" });
  await expect(lyricsBtn).toBeVisible({ timeout: 5000 });
  await lyricsBtn.click();
  // 歌詞パネルが表示される（LyricsPanel の lyrics-panel-overlay クラスを確認）
  await expect(page.locator(".lyrics-panel-overlay")).toBeVisible({ timeout: 3000 });
});

test("P-04: 再生ボタンが存在して操作可能", async ({ page }) => {
  // フローティングバーの再生ボタンが存在する（チャンネル未選択時は再生はできないが操作可能）
  const playBtn = page.locator(".fb-play-btn");
  await expect(playBtn).toBeVisible({ timeout: 5000 });
  // 再生ボタンのaria-labelを確認
  await expect(playBtn).toHaveAttribute("aria-label", /(再生|一時停止)/);
});
