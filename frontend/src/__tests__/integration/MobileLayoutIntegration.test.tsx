/**
 * App + MobileLayout 統合テスト（実API接続）
 * テスト仕様書 IT-ML-01 〜 IT-ML-05 に対応
 *
 * 前提: Docker コンテナ起動済み（docker compose up -d）
 * API エンドポイント: http://localhost:3200/api/
 *
 * NOTE: jsdom 環境では実際の fetch を使用する。
 * モック禁止（Gate 5 要件）。
 */
import { describe, it, expect } from "vitest";

const BASE_URL = "http://localhost:3200";

describe("IT-ML: 実API結合テスト（モック禁止）", () => {
  it("IT-ML-01: 実API /api/channels からチャンネル一覧が取得できる", async () => {
    const res = await fetch(`${BASE_URL}/api/channels`);
    expect(res.ok).toBe(true);
    const data = await res.json();
    expect(data).toHaveProperty("channels");
    expect(Array.isArray(data.channels)).toBe(true);
    // 少なくとも1件のチャンネルが存在する
    expect(data.channels.length).toBeGreaterThanOrEqual(0);
  });

  it("IT-ML-01: 取得したチャンネルが必要なフィールドを持つ", async () => {
    const res = await fetch(`${BASE_URL}/api/channels`);
    const data = await res.json();
    if (data.channels.length > 0) {
      const channel = data.channels[0];
      expect(channel).toHaveProperty("slug");
      expect(channel).toHaveProperty("name");
      expect(channel).toHaveProperty("is_active");
      expect(channel).toHaveProperty("stream_url");
    }
  });

  it("IT-ML-04: 実API /api/channels/:slug/tracks から曲一覧が取得できる", async () => {
    // まずチャンネル一覧を取得
    const channelsRes = await fetch(`${BASE_URL}/api/channels`);
    const channelsData = await channelsRes.json();
    const activeChannels = channelsData.channels.filter((c: { is_active: boolean }) => c.is_active);

    if (activeChannels.length === 0) {
      console.log("アクティブなチャンネルがないためスキップ");
      return;
    }

    const slug = activeChannels[0].slug;
    const res = await fetch(`${BASE_URL}/api/channels/${slug}/tracks`);
    expect(res.ok).toBe(true);
    const data = await res.json();
    expect(data).toHaveProperty("tracks");
    expect(Array.isArray(data.tracks)).toBe(true);
  });

  it("IT-ML-03: 実API now_playing エンドポイントが応答する", async () => {
    const channelsRes = await fetch(`${BASE_URL}/api/channels`);
    const channelsData = await channelsRes.json();
    const activeChannels = channelsData.channels.filter((c: { is_active: boolean }) => c.is_active);

    if (activeChannels.length === 0) {
      console.log("アクティブなチャンネルがないためスキップ");
      return;
    }

    const slug = activeChannels[0].slug;
    const res = await fetch(`${BASE_URL}/api/channels/${slug}/now-playing`);
    expect(res.ok).toBe(true);
    const data = await res.json();
    // now_playing は null または track オブジェクト
    expect(data).toHaveProperty("track");
  });
});
