/**
 * E2E テスト: モバイルフロー
 * テスト仕様書 シナリオ M-01 〜 M-05 に対応
 * viewport: 390x844 (iPhone 14 Pro)
 */
import { test, expect } from "@playwright/test";

test.use({
  viewport: { width: 390, height: 844 },
});

test.beforeEach(async ({ page }) => {
  await page.goto("/");
  await page.waitForLoadState("networkidle");
});

test("M-01: ホーム → タブバーが表示される", async ({ page }) => {
  // タブバーが存在することを確認
  await expect(page.getByRole("tablist")).toBeVisible();
  // RADIO タブが表示される
  await expect(page.getByRole("tab", { name: /RADIO/i })).toBeVisible();
  await expect(page.getByRole("tab", { name: /TRACKS/i })).toBeVisible();
  await expect(page.getByRole("tab", { name: /LIKES/i })).toBeVisible();
});

test("M-01: ホーム → RADIO タブが初期アクティブ", async ({ page }) => {
  const radioTab = page.getByRole("tab", { name: /RADIO/i });
  await expect(radioTab).toHaveAttribute("aria-selected", "true");
});

test("M-01: ホーム → チャンネルカードグリッドが表示される", async ({ page }) => {
  // チャンネル選択エリアが存在する
  const channelGrid = page.getByRole("radiogroup", { name: "チャンネル選択" });
  await expect(channelGrid).toBeVisible();
});

test("M-01: ヘッダーに AI Music Station タイトルが表示される", async ({ page }) => {
  await expect(page.getByText("AI Music Station")).toBeVisible();
});

test("M-02: チャンネル選択 → ミニプレイヤーが表示される", async ({ page }) => {
  // チャンネルカードをクリック
  const channelCards = page.locator(".mobile-channel-card");
  const count = await channelCards.count();

  if (count > 0) {
    await channelCards.first().click();
    // ミニプレイヤーが表示される
    await expect(page.locator(".miniplayer")).toBeVisible({ timeout: 5000 });
    // 再生ボタンが存在する
    await expect(page.getByRole("button", { name: /再生|一時停止/ })).toBeVisible();
  }
});

test("M-04: TRACKS タブクリック → 再生履歴が表示される", async ({ page }) => {
  const tracksTab = page.getByRole("tab", { name: /TRACKS/i });
  await tracksTab.click();
  // タブが切り替わる
  await expect(tracksTab).toHaveAttribute("aria-selected", "true");
  // 「再生履歴」または「チャンネルを選択してください」が表示される
  const hasHistory = await page.locator(".mobile-tracks-tab").isVisible();
  expect(hasHistory).toBe(true);
});

test("M-05: チャンネル管理ボタンをタップ → 管理画面に遷移", async ({ page }) => {
  // ヘッダー内のチャンネル管理ボタン（mobile-manage-btn）をクリック
  const manageBtn = page.locator(".mobile-manage-btn");
  await expect(manageBtn).toBeVisible();
  await manageBtn.click();
  // ChannelManager コンポーネントのヘッダーが表示される
  // ChannelManager の h2 見出しが表示される
  await expect(page.locator("h2").filter({ hasText: "チャンネル管理" })).toBeVisible({ timeout: 5000 });
});
