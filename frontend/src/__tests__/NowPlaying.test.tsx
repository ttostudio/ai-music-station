import { render, screen, cleanup } from "@testing-library/react";
import { describe, it, expect, afterEach } from "vitest";
import { NowPlaying } from "../components/NowPlaying";
import type { Track } from "../api/types";

afterEach(cleanup);

const mockTrack: Track = {
  id: "1",
  caption: "雨の日のローファイビート",
  duration_ms: 180000,
  bpm: 85,
  music_key: "Am",
  instrumental: true,
  play_count: 3,
  like_count: 0,
  created_at: "2026-03-21T10:00:00Z",
};

describe("NowPlaying", () => {
  it("shows placeholder when no track", () => {
    render(<NowPlaying track={null} />);
    // FR-108-2: 未選択時メッセージを変更
    expect(
      screen.getAllByText(/チャンネルを選択して再生を開始してください/).length,
    ).toBeGreaterThan(0);
  });

  it("shows track caption", () => {
    render(<NowPlaying track={mockTrack} />);
    expect(
      screen.getAllByText("雨の日のローファイビート").length,
    ).toBeGreaterThan(0);
  });

  it("shows BPM", () => {
    render(<NowPlaying track={mockTrack} />);
    expect(screen.getAllByText("85 BPM").length).toBeGreaterThan(0);
  });

  it("shows key", () => {
    render(<NowPlaying track={mockTrack} />);
    expect(screen.getAllByText("キー: Am").length).toBeGreaterThan(0);
  });

  it("shows instrumental label", () => {
    render(<NowPlaying track={mockTrack} />);
    expect(screen.getAllByText("インスト").length).toBeGreaterThan(0);
  });
});
