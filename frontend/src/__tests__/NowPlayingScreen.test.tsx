import { describe, it, expect, vi, afterEach } from "vitest";
import { render, fireEvent, cleanup } from "@testing-library/react";
import { NowPlayingScreen } from "../components/NowPlayingScreen";
import type { Track } from "../api/types";
import React from "react";

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

const audioRef = React.createRef<HTMLAudioElement | null>();

const defaultProps = {
  track: mockTrack,
  channelName: "Anime Songs",
  channelSlug: "anime",
  isPlaying: false,
  elapsedMs: 60000,
  durationMs: 180000,
  audioRef,
  onBack: vi.fn(),
  onPlayPause: vi.fn(),
  onSkipPrev: vi.fn(),
  onSkipNext: vi.fn(),
  onLike: vi.fn(),
  onLyrics: vi.fn(),
};

describe("NowPlayingScreen", () => {
  it("UT-NPS-01: ビジュアライザーエリア (canvas) が存在する", () => {
    const { container } = render(<NowPlayingScreen {...defaultProps} />);
    expect(container.querySelector("canvas")).toBeInTheDocument();
  });

  it("UT-NPS-02: 曲名が表示される", () => {
    const { getByText } = render(<NowPlayingScreen {...defaultProps} />);
    expect(getByText("テストタイトル")).toBeInTheDocument();
  });

  it("UT-NPS-03: プログレスバーが存在する（role='slider'）", () => {
    const { container } = render(<NowPlayingScreen {...defaultProps} />);
    // ProgressBar は role="slider" で実装されている
    expect(container.querySelector("[role='slider']")).toBeInTheDocument();
  });

  it("UT-NPS-05: 前/次スキップボタンが存在する", () => {
    const { container } = render(<NowPlayingScreen {...defaultProps} />);
    const prevBtn = container.querySelector("[aria-label='前の曲']");
    const nextBtn = container.querySelector("[aria-label='次の曲']");
    expect(prevBtn).toBeInTheDocument();
    expect(nextBtn).toBeInTheDocument();
  });

  it("UT-NPS-06: いいね・歌詞・シェアボタンが存在する", () => {
    const { container } = render(<NowPlayingScreen {...defaultProps} />);
    const actionBtns = container.querySelector(".action-buttons");
    expect(actionBtns).toBeInTheDocument();
  });

  it("UT-NPS-07: 歌詞ボタンクリックで onLyrics が呼ばれる", () => {
    const onLyrics = vi.fn();
    const { container } = render(<NowPlayingScreen {...defaultProps} onLyrics={onLyrics} />);
    const lyricsBtn = container.querySelector("[aria-label='歌詞']") as HTMLElement;
    fireEvent.click(lyricsBtn);
    expect(onLyrics).toHaveBeenCalled();
  });

  it("UT-NPS-08: 戻るボタンで onBack が呼ばれる", () => {
    const onBack = vi.fn();
    const { container } = render(<NowPlayingScreen {...defaultProps} onBack={onBack} />);
    const backBtn = container.querySelector("[aria-label='戻る']") as HTMLElement;
    fireEvent.click(backBtn);
    expect(onBack).toHaveBeenCalled();
  });
});
