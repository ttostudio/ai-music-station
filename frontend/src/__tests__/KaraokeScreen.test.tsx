import { describe, it, expect, vi, afterEach } from "vitest";
import { render, fireEvent, cleanup } from "@testing-library/react";
import { KaraokeScreen } from "../components/KaraokeScreen";
import type { Track } from "../api/types";

afterEach(cleanup);

const mockTrack: Track = {
  id: "1",
  caption: "テスト曲",
  title: "テストタイトル",
  lyrics: "[00:01.00]過去の歌詞\n[00:05.00]現在の歌詞\n[00:10.00]未来の歌詞",
  duration_ms: 30000,
  bpm: 120,
  music_key: "C",
  instrumental: false,
  play_count: 10,
  like_count: 5,
  created_at: "2026-03-24T00:00:00Z",
};

describe("KaraokeScreen", () => {
  it("UT-KS-01: 歌詞ありの場合 karaoke-hero-area が表示される", () => {
    const { container } = render(
      <KaraokeScreen
        track={mockTrack}
        isPlaying={false}
        elapsedMs={5000}
        durationMs={30000}
        onClose={vi.fn()}
        onPlayPause={vi.fn()}
      />
    );
    expect(container.querySelector(".karaoke-hero-area")).toBeInTheDocument();
  });

  it("UT-KS-06: × ボタンクリックで onClose が呼ばれる", () => {
    const onClose = vi.fn();
    const { container } = render(
      <KaraokeScreen
        track={mockTrack}
        isPlaying={false}
        elapsedMs={5000}
        durationMs={30000}
        onClose={onClose}
        onPlayPause={vi.fn()}
      />
    );
    // aria-label="閉じる" のボタン
    const closeBtn = container.querySelector("[aria-label='閉じる']") as HTMLElement;
    fireEvent.click(closeBtn);
    expect(onClose).toHaveBeenCalled();
  });

  it("UT-KS-07: ミニプレイヤーが下部に表示される", () => {
    const { container } = render(
      <KaraokeScreen
        track={mockTrack}
        isPlaying={false}
        elapsedMs={5000}
        durationMs={30000}
        onClose={vi.fn()}
        onPlayPause={vi.fn()}
      />
    );
    expect(container.querySelector(".karaoke-mini-player")).toBeInTheDocument();
  });

  it("停止中は aria-label='再生' のボタンが存在する", () => {
    const { container } = render(
      <KaraokeScreen
        track={mockTrack}
        isPlaying={false}
        elapsedMs={5000}
        durationMs={30000}
        onClose={vi.fn()}
        onPlayPause={vi.fn()}
      />
    );
    const playBtn = container.querySelector("[aria-label='再生']");
    expect(playBtn).toBeInTheDocument();
  });

  it("再生中は aria-label='一時停止' のボタンが存在する", () => {
    const { container } = render(
      <KaraokeScreen
        track={mockTrack}
        isPlaying={true}
        elapsedMs={5000}
        durationMs={30000}
        onClose={vi.fn()}
        onPlayPause={vi.fn()}
      />
    );
    const pauseBtn = container.querySelector("[aria-label='一時停止']");
    expect(pauseBtn).toBeInTheDocument();
  });

  it("歌詞なしの場合は karaoke-hero-area が表示されない", () => {
    const trackWithoutLyrics = { ...mockTrack, lyrics: "" };
    const { container } = render(
      <KaraokeScreen
        track={trackWithoutLyrics}
        isPlaying={false}
        elapsedMs={5000}
        durationMs={30000}
        onClose={vi.fn()}
        onPlayPause={vi.fn()}
      />
    );
    expect(container.querySelector(".karaoke-hero-area")).not.toBeInTheDocument();
  });
});
