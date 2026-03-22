import { render, screen, cleanup } from "@testing-library/react";
import { describe, it, expect, afterEach, vi } from "vitest";
import { Player } from "../components/Player";

afterEach(cleanup);

const defaultProps = {
  volume: 0.8,
  onVolumeChange: vi.fn(),
  isPlaying: false,
  onTogglePlay: vi.fn(),
};

describe("Player", () => {
  it("renders channel name", () => {
    render(<Player streamUrl="/stream/lofi.ogg" channelName="LoFi ビーツ" {...defaultProps} />);
    expect(screen.getAllByText("LoFi ビーツ").length).toBeGreaterThan(0);
  });

  it("shows placeholder when no channel selected", () => {
    render(<Player streamUrl={null} channelName="" {...defaultProps} />);
    expect(
      screen.getAllByText("チャンネルを選択してください").length,
    ).toBeGreaterThan(0);
  });

  it("has play button", () => {
    render(<Player streamUrl="/stream/lofi.ogg" channelName="LoFi" {...defaultProps} />);
    expect(screen.getAllByLabelText("再生").length).toBeGreaterThan(0);
  });

  it("has volume slider", () => {
    render(<Player streamUrl="/stream/lofi.ogg" channelName="LoFi" {...defaultProps} />);
    expect(screen.getAllByLabelText("音量").length).toBeGreaterThan(0);
  });

  it("disables play button when no stream", () => {
    render(<Player streamUrl={null} channelName="" {...defaultProps} />);
    const btns = screen.getAllByLabelText("再生");
    expect(btns[0]).toBeDisabled();
  });

  it("shows now playing track title", () => {
    const track = {
      id: "1",
      caption: "テストキャプション",
      title: "夕暮れの散歩道",
      duration_ms: 180000,
      bpm: 85,
      music_key: "Am",
      instrumental: false,
      play_count: 3,
      like_count: 1,
      created_at: "2026-03-21T10:00:00Z",
    };
    render(
      <Player streamUrl="/stream/anime.ogg" channelName="Anime Songs" nowPlaying={track} {...defaultProps} />,
    );
    expect(screen.getAllByText("夕暮れの散歩道").length).toBeGreaterThan(0);
  });

  it("shows caption when no title in now playing", () => {
    const track = {
      id: "1",
      caption: "テストキャプション",
      duration_ms: 180000,
      bpm: 85,
      music_key: "Am",
      instrumental: false,
      play_count: 3,
      like_count: 0,
      created_at: "2026-03-21T10:00:00Z",
    };
    render(
      <Player streamUrl="/stream/anime.ogg" channelName="Anime Songs" nowPlaying={track} {...defaultProps} />,
    );
    expect(screen.getAllByText("テストキャプション").length).toBeGreaterThan(0);
  });

  it("does not show track info when nowPlaying is null", () => {
    render(<Player streamUrl="/stream/anime.ogg" channelName="Anime Songs" nowPlaying={null} {...defaultProps} />);
    expect(screen.queryByText("夕暮れの散歩道")).toBeNull();
  });
});
