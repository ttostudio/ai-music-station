import { describe, it, expect, vi, afterEach } from "vitest";
import { render, fireEvent, cleanup } from "@testing-library/react";
import { MiniPlayer } from "../components/MiniPlayer";
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

describe("MiniPlayer", () => {
  it("UT-MP-01: track null 時にデフォルトメッセージが表示される", () => {
    const { getByText } = render(
      <MiniPlayer
        track={null}
        channelName="テストチャンネル"
        isPlaying={false}
        onPlayPause={vi.fn()}
        onOpenNowPlaying={vi.fn()}
      />
    );
    expect(getByText("再生を開始してください")).toBeInTheDocument();
  });

  it("UT-MP-02: 曲名とチャンネル名が表示される", () => {
    const { getByText } = render(
      <MiniPlayer
        track={mockTrack}
        channelName="Anime Songs"
        isPlaying={false}
        onPlayPause={vi.fn()}
        onOpenNowPlaying={vi.fn()}
      />
    );
    expect(getByText("テストタイトル")).toBeInTheDocument();
    expect(getByText("Anime Songs")).toBeInTheDocument();
  });

  it("UT-MP-03: 再生ボタンクリックで onPlayPause が呼ばれる", () => {
    const onPlayPause = vi.fn();
    const { container } = render(
      <MiniPlayer
        track={mockTrack}
        channelName="Anime Songs"
        isPlaying={false}
        onPlayPause={onPlayPause}
        onOpenNowPlaying={vi.fn()}
      />
    );
    // クラス名でボタンを特定
    const playBtn = container.querySelector(".miniplayer-play-btn") as HTMLElement;
    fireEvent.click(playBtn);
    expect(onPlayPause).toHaveBeenCalled();
  });

  it("UT-MP-04: 再生中は一時停止アイコン（aria-label='一時停止'）", () => {
    const { container } = render(
      <MiniPlayer
        track={mockTrack}
        channelName="Anime Songs"
        isPlaying={true}
        onPlayPause={vi.fn()}
        onOpenNowPlaying={vi.fn()}
      />
    );
    const playBtn = container.querySelector(".miniplayer-play-btn") as HTMLElement;
    expect(playBtn).toHaveAttribute("aria-label", "一時停止");
  });

  it("UT-MP-06: 再生ボタンに aria-label='再生' が付与される（停止中）", () => {
    const { container } = render(
      <MiniPlayer
        track={mockTrack}
        channelName="Anime Songs"
        isPlaying={false}
        onPlayPause={vi.fn()}
        onOpenNowPlaying={vi.fn()}
      />
    );
    const playBtn = container.querySelector(".miniplayer-play-btn") as HTMLElement;
    expect(playBtn).toHaveAttribute("aria-label", "再生");
  });

  it("UT-MP-07: 曲名エリアクリックで onOpenNowPlaying が呼ばれる", () => {
    const onOpenNowPlaying = vi.fn();
    const { container } = render(
      <MiniPlayer
        track={mockTrack}
        channelName="Anime Songs"
        isPlaying={false}
        onPlayPause={vi.fn()}
        onOpenNowPlaying={onOpenNowPlaying}
      />
    );
    const miniplayerContainer = container.querySelector(".miniplayer") as HTMLElement;
    fireEvent.click(miniplayerContainer);
    expect(onOpenNowPlaying).toHaveBeenCalled();
  });
});
