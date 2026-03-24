import { describe, it, expect, vi, afterEach } from "vitest";
import { render, fireEvent, cleanup } from "@testing-library/react";
import { FloatingBar } from "../components/FloatingBar";
import type { Track } from "../api/types";

afterEach(cleanup);

const mockTrack: Track = {
  id: "1",
  caption: "テスト曲",
  title: "テストタイトル",
  duration_ms: 180000,
  bpm: 120,
  music_key: "C",
  instrumental: false,
  play_count: 10,
  like_count: 5,
  created_at: "2026-03-24T00:00:00Z",
};

const defaultProps = {
  track: mockTrack,
  channelName: "Anime Songs",
  isPlaying: false,
  elapsedMs: 60000,
  durationMs: 180000,
  lyricsActive: false,
  onPlayPause: vi.fn(),
  onLike: vi.fn(),
  onLyricsToggle: vi.fn(),
  onChannelMenu: vi.fn(),
};

describe("FloatingBar", () => {
  it("UT-FB-01: 再生ボタンが描画される", () => {
    const { container } = render(<FloatingBar {...defaultProps} />);
    const playBtn = container.querySelector(".fb-play-btn") as HTMLElement;
    expect(playBtn).toBeInTheDocument();
    expect(playBtn).toHaveAttribute("aria-label", "再生");
  });

  it("UT-FB-02: 曲名が表示される", () => {
    const { container } = render(<FloatingBar {...defaultProps} />);
    const titleEl = container.querySelector(".fb-title") as HTMLElement;
    expect(titleEl?.textContent).toBe("テストタイトル");
  });

  it("UT-FB-04: いいねボタンが存在する", () => {
    const { container } = render(<FloatingBar {...defaultProps} />);
    const btns = container.querySelectorAll(".fb-icon-btn");
    const likeBtn = Array.from(btns).find(b => b.getAttribute("aria-label")?.includes("いいね"));
    expect(likeBtn).toBeInTheDocument();
  });

  it("UT-FB-05: 歌詞トグルボタンが存在する", () => {
    const { container } = render(<FloatingBar {...defaultProps} />);
    const btns = container.querySelectorAll(".fb-icon-btn");
    const lyricsBtn = Array.from(btns).find(b => b.getAttribute("aria-label") === "歌詞パネル");
    expect(lyricsBtn).toBeInTheDocument();
  });

  it("UT-FB-06: チャンネルメニューボタンが存在する", () => {
    const { container } = render(<FloatingBar {...defaultProps} />);
    const channelBtn = container.querySelector(".fb-channel-btn") as HTMLElement;
    expect(channelBtn).toBeInTheDocument();
  });

  it("UT-FB-07: 歌詞トグルクリックで onLyricsToggle が呼ばれる", () => {
    const onLyricsToggle = vi.fn();
    const { container } = render(<FloatingBar {...defaultProps} onLyricsToggle={onLyricsToggle} />);
    const btns = container.querySelectorAll(".fb-icon-btn");
    const lyricsBtn = Array.from(btns).find(b => b.getAttribute("aria-label") === "歌詞パネル") as HTMLElement;
    fireEvent.click(lyricsBtn);
    expect(onLyricsToggle).toHaveBeenCalled();
  });

  it("UT-FB-08: チャンネルメニュークリックで onChannelMenu が呼ばれる", () => {
    const onChannelMenu = vi.fn();
    const { container } = render(<FloatingBar {...defaultProps} onChannelMenu={onChannelMenu} />);
    const channelBtn = container.querySelector(".fb-channel-btn") as HTMLElement;
    fireEvent.click(channelBtn);
    expect(onChannelMenu).toHaveBeenCalled();
  });

  it("再生中は一時停止ボタンが表示される", () => {
    const { container } = render(<FloatingBar {...defaultProps} isPlaying={true} />);
    const playBtn = container.querySelector(".fb-play-btn") as HTMLElement;
    expect(playBtn).toHaveAttribute("aria-label", "一時停止");
  });
});
