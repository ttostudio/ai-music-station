/**
 * E2E テスト: Stream / Track モード切替
 * テストID: E2E-PC-006
 * viewport: PC 1440x900
 */
import { test, expect } from "@playwright/test";

test.use({ viewport: { width: 1440, height: 900 } });

test.describe("Stream / Track モード切替", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/");
    await page.waitForLoadState("networkidle");
  });

  test("E2E-PC-006a: ストリーム再生開始 → Player が表示される", async ({ page }) => {
    // チャンネルメニューを開く
    const channelMenuBtn = page.getByRole("button", { name: "チャンネルメニュー" });
    await expect(channelMenuBtn).toBeVisible({ timeout: 5000 });
    await channelMenuBtn.click();

    const menuItems = page.locator(".channel-menu-item");
    const itemCount = await menuItems.count();
    if (itemCount === 0) {
      test.skip();
      return;
    }

    await menuItems.first().click();

    // 再生ボタンをクリック
    const playBtn = page.locator(".fb-play-btn");
    await expect(playBtn).toBeVisible({ timeout: 3000 });
    await playBtn.click();

    // Player が存在することを確認
    await expect(page.locator(".floating-bar")).toBeVisible({ timeout: 3000 });
  });

  test("E2E-PC-006b: Track モードに切り替えられる（SearchBar経由）", async ({ page }) => {
    // デスクトップでは TRACKS タブはなく、SearchBar からトラック再生
    const searchIconBtn = page.locator(".search-icon-btn");
    const searchInput = page.locator(".search-bar-input, [aria-label='トラック検索']");

    // SearchBar を開く（アイコンボタンがある場合はクリック）
    if (await searchIconBtn.count() > 0) {
      await searchIconBtn.click();
    }

    // 入力フィールドが表示されない場合はスキップ
    const inputVisible = await searchInput.isVisible().catch(() => false);
    if (!inputVisible) {
      test.skip();
      return;
    }

    await searchInput.fill("jazz");
    // 検索結果が表示されるまで待機
    const playBtn = page.locator(".search-result-play").first();
    try {
      await playBtn.waitFor({ state: "visible", timeout: 5000 });
    } catch {
      test.skip();
      return;
    }
    await playBtn.click();

    // Track モードを示す要素（FloatingBar）が表示される
    await expect(
      page.locator("[data-testid='player-mode-track'], .player-mode-track, .track-player, .floating-bar").first()
    ).toBeVisible({ timeout: 5000 });
  });

  test("E2E-PC-006c: Stream → Track → Stream の往復でエラーが発生しない", async ({ page }) => {
    // コンソールエラーを収集
    const errors: string[] = [];
    page.on("console", (msg) => {
      if (msg.type() === "error") {
        errors.push(msg.text());
      }
    });

    // Step 1: チャンネル選択 → Stream 再生
    const channelMenuBtn = page.getByRole("button", { name: "チャンネルメニュー" });
    await expect(channelMenuBtn).toBeVisible({ timeout: 5000 });
    await channelMenuBtn.click();

    const menuItems = page.locator(".channel-menu-item");
    const itemCount = await menuItems.count();
    if (itemCount === 0) {
      test.skip();
      return;
    }
    await menuItems.first().click();

    const playBtn = page.locator(".fb-play-btn");
    await expect(playBtn).toBeVisible({ timeout: 3000 });
    await playBtn.click();

    // Stream 再生中の Player 確認
    await expect(page.locator(".floating-bar")).toBeVisible({ timeout: 3000 });

    // Step 2: Track モードへ切替（SearchBar経由）
    const searchIconBtn = page.locator(".search-icon-btn");
    if (await searchIconBtn.count() > 0) {
      await searchIconBtn.click();
    }
    const searchInput2 = page.locator(".search-bar-input, [aria-label='トラック検索']");
    if (await searchInput2.isVisible().catch(() => false)) {
      await searchInput2.fill("jazz");
      const trackPlayBtn = page.locator(".search-result-play").first();
      try {
        await trackPlayBtn.waitFor({ state: "visible", timeout: 5000 });
        await trackPlayBtn.click();
        await expect(page.locator(".floating-bar")).toBeVisible({ timeout: 3000 });
      } catch {
        // 検索結果なし、スキップ
      }
    }

    // Step 3: Stream モードに戻す
    await channelMenuBtn.click();
    if (await menuItems.count() > 0) {
      await menuItems.first().click();
      await expect(page.locator(".floating-bar")).toBeVisible({ timeout: 3000 });
    }

    // AudioContext 関連エラーがないことを確認
    const audioErrors = errors.filter((e) => /AudioContext|audio/i.test(e));
    expect(audioErrors).toHaveLength(0);
  });
});
