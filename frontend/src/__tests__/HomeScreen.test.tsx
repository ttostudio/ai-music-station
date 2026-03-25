/**
 * HomeScreen テスト（MobileLayout の RADIO タブ = ホーム画面）
 * テスト仕様書 UT-HS-01 〜 UT-HS-05 に対応
 */
import { describe, it, expect, vi, afterEach } from "vitest";
import { render, fireEvent, cleanup } from "@testing-library/react";
import { MobileLayout } from "../components/layouts/MobileLayout";
import type { Channel, Track } from "../api/types";
import React from "react";

afterEach(cleanup);

const mockChannels: Channel[] = [
  {
    id: "1",
    slug: "anime",
    name: "Anime Songs",
    description: null,
    is_active: true,
    queue_depth: 2,
    total_tracks: 50,
    stream_url: "http://example.com/anime",
    now_playing: null,
  },
  {
    id: "2",
    slug: "jazz",
    name: "Jazz Vibes",
    description: null,
    is_active: true,
    queue_depth: 0,
    total_tracks: 30,
    stream_url: "http://example.com/jazz",
    now_playing: null,
  },
];

const audioRef = React.createRef<HTMLAudioElement | null>();

const defaultProps = {
  channels: mockChannels,
  activeSlug: null,
  activeChannel: undefined,
  track: null,
  isPlaying: false,
  elapsedMs: 0,
  durationMs: 0,
  audioRef,
  activeTab: "radio" as const,
  currentScreen: "home" as const,
  onTabChange: vi.fn(),
  onScreenChange: vi.fn(),
  onSelectChannel: vi.fn(),
  onTogglePlay: vi.fn(),
  onSkipPrev: vi.fn(),
  onSkipNext: vi.fn(),
  onLike: vi.fn(),
};

describe("HomeScreen (MobileLayout RADIO tab)", () => {
  it("UT-HS-01: ヘッダーに「AI Music Station」テキストが存在する", () => {
    const { getByText } = render(<MobileLayout {...defaultProps} />);
    expect(getByText("AI Music Station")).toBeInTheDocument();
  });

  it("UT-HS-02: チャンネルカードグリッドが表示される", () => {
    const { container, getAllByText } = render(<MobileLayout {...defaultProps} />);
    expect(container.querySelector(".mobile-channel-grid")).toBeInTheDocument();
    expect(getAllByText("Anime Songs").length).toBeGreaterThan(0);
    expect(getAllByText("Jazz Vibes").length).toBeGreaterThan(0);
  });

  it("UT-HS-03: チャンネル選択でonSelectChannelが呼ばれる", () => {
    const onSelectChannel = vi.fn();
    const { container } = render(<MobileLayout {...defaultProps} onSelectChannel={onSelectChannel} />);
    const cards = container.querySelectorAll(".mobile-channel-card");
    fireEvent.click(cards[0]);
    expect(onSelectChannel).toHaveBeenCalledWith("anime");
  });

  it("UT-HS-04: 「チャンネル管理」ボタンが存在する", () => {
    const { getByText } = render(<MobileLayout {...defaultProps} />);
    expect(getByText("チャンネル管理")).toBeInTheDocument();
  });

  it("UT-HS-03: チャンネル選択後はミニプレイヤーが表示される", () => {
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
    const { container } = render(
      <MobileLayout
        {...defaultProps}
        activeSlug="anime"
        activeChannel={mockChannels[0]}
        track={mockTrack}
      />
    );
    expect(container.querySelector(".miniplayer")).toBeInTheDocument();
  });
});
