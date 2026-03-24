/**
 * E2E テスト: レスポンシブ・ブレークポイント確認
 * テスト仕様書 RT-01 〜 RT-06 に対応
 */
import { test, expect } from "@playwright/test";

test("RT-01: 767px viewport → タブバーが表示される", async ({ page }) => {
  await page.setViewportSize({ width: 767, height: 844 });
  await page.goto("/");
  await page.waitForLoadState("networkidle");
  await expect(page.locator(".tabbar-outer")).toBeVisible({ timeout: 5000 });
});

test("RT-02: 767px viewport → フローティングバーが表示されない", async ({ page }) => {
  await page.setViewportSize({ width: 767, height: 844 });
  await page.goto("/");
  await page.waitForLoadState("networkidle");
  await expect(page.locator(".floating-bar")).not.toBeVisible();
});

test("RT-05: 1024px viewport → フローティングバーが表示される", async ({ page }) => {
  await page.setViewportSize({ width: 1024, height: 768 });
  await page.goto("/");
  await page.waitForLoadState("networkidle");
  await expect(page.locator(".floating-bar")).toBeVisible({ timeout: 5000 });
});

test("RT-06: 1024px viewport → タブバーが表示されない", async ({ page }) => {
  await page.setViewportSize({ width: 1024, height: 768 });
  await page.goto("/");
  await page.waitForLoadState("networkidle");
  await expect(page.locator(".tabbar-outer")).not.toBeVisible();
});

test("スクリーンショット: SS-01 モバイル ホーム画面", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/");
  await page.waitForLoadState("networkidle");
  await expect(page).toHaveScreenshot("home-mobile.png", { threshold: 0.1 });
});

test("スクリーンショット: SS-06 PC シアター型", async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 900 });
  await page.goto("/");
  await page.waitForLoadState("networkidle");
  await expect(page).toHaveScreenshot("home-pc.png", { threshold: 0.1 });
});
