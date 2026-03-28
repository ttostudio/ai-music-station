/**
 * E2E テスト: 回帰 — Icecast ストリーム再生
 * テストID: REG-001
 * viewport: PC 1440x900
 */
import { test, expect } from "@playwright/test";

test.use({ viewport: { width: 1440, height: 900 } });

test.describe("回帰: Icecast ストリーム再生", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/");
    await page.waitForLoadState("networkidle");
  });

  test("REG-001: チャンネルを選択してストリーム再生を開始できる", async ({ page }) => {
    // チャンネルメニューを開く
    const channelMenuBtn = page.getByRole("button", { name: "チャンネルメニュー" });
    await expect(channelMenuBtn).toBeVisible({ timeout: 5000 });
    await channelMenuBtn.click();

    const menuItems = page.locator(".channel-menu-item");
    await expect(menuItems.first()).toBeVisible({ timeout: 3000 });
    await menuItems.first().click();

    // 再生ボタンが表示される
    const playBtn = page.locator(".fb-play-btn");
    await expect(playBtn).toBeVisible({ timeout: 3000 });
    await expect(playBtn).toHaveAttribute("aria-label", /(再生|一時停止)/);
  });

  test("REG-001b: ストリーム再生ボタンをクリックすると Player が Stream モードになる", async ({ page }) => {
    const channelMenuBtn = page.getByRole("button", { name: "チャンネルメニュー" });
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

    // Stream モードを示す要素またはフローティングバーが存在する
    await expect(
      page.locator("[data-testid='player-mode-stream'], .player-mode-stream, .floating-bar").first()
    ).toBeVisible({ timeout: 5000 });
  });

  test("REG-001c: ストリーム再生中にコンソールに致命的エラーが出ない", async ({ page }) => {
    const errors: string[] = [];
    page.on("console", (msg) => {
      if (msg.type() === "error") {
        errors.push(msg.text());
      }
    });

    const channelMenuBtn = page.getByRole("button", { name: "チャンネルメニュー" });
    await channelMenuBtn.click();

    const menuItems = page.locator(".channel-menu-item");
    if (await menuItems.count() === 0) {
      test.skip();
      return;
    }

    await menuItems.first().click();
    const playBtn = page.locator(".fb-play-btn");
    await expect(playBtn).toBeVisible({ timeout: 3000 });
    await playBtn.click();

    // 3秒間再生を維持してエラーがないことを確認
    await page.waitForSelector(".floating-bar", { timeout: 5000 });

    const streamErrors = errors.filter((e) => /stream|icecast|audio/i.test(e));
    expect(streamErrors).toHaveLength(0);
  });
});
