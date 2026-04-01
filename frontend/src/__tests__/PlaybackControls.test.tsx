import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { PlaybackControls } from "../components/PlaybackControls";

describe("PlaybackControls", () => {
  const defaultProps = {
    isPlaying: false,
    onPlayPause: vi.fn(),
    onSkipPrev: vi.fn(),
    onSkipNext: vi.fn(),
  };

  it("基本ボタンが表示される", () => {
    render(<PlaybackControls {...defaultProps} />);
    expect(screen.getByLabelText("再生")).toBeInTheDocument();
    expect(screen.getByLabelText("前の曲")).toBeInTheDocument();
    expect(screen.getByLabelText("次の曲")).toBeInTheDocument();
  });

  it("再生中は一時停止ボタンが表示される", () => {
    render(<PlaybackControls {...defaultProps} isPlaying={true} />);
    expect(screen.getByLabelText("一時停止")).toBeInTheDocument();
  });

  it("shuffle/repeat props がない時はボタンが非表示", () => {
    render(<PlaybackControls {...defaultProps} />);
    expect(screen.queryByLabelText(/シャッフル/)).toBeNull();
    expect(screen.queryByLabelText(/リピート/)).toBeNull();
  });

  it("onToggleShuffle があるときシャッフルボタンが表示される", () => {
    const onToggleShuffle = vi.fn();
    render(
      <PlaybackControls
        {...defaultProps}
        shuffle={false}
        onToggleShuffle={onToggleShuffle}
      />
    );
    const btn = screen.getByLabelText("シャッフルをオンにする");
    expect(btn).toBeInTheDocument();
    fireEvent.click(btn);
    expect(onToggleShuffle).toHaveBeenCalledOnce();
  });

  it("shuffle=true 時にシャッフルボタンがアクティブ状態", () => {
    render(
      <PlaybackControls
        {...defaultProps}
        shuffle={true}
        onToggleShuffle={vi.fn()}
      />
    );
    const btn = screen.getByLabelText("シャッフルをオフにする");
    expect(btn).toHaveClass("playback-mode-btn--active");
  });

  it("onCycleRepeat があるときリピートボタンが表示される", () => {
    const onCycleRepeat = vi.fn();
    render(
      <PlaybackControls
        {...defaultProps}
        repeatMode="off"
        onCycleRepeat={onCycleRepeat}
      />
    );
    const btn = screen.getByLabelText("リピートをオンにする");
    expect(btn).toBeInTheDocument();
    fireEvent.click(btn);
    expect(onCycleRepeat).toHaveBeenCalledOnce();
  });

  it("repeatMode=all 時にリピートボタンがアクティブ", () => {
    render(
      <PlaybackControls
        {...defaultProps}
        repeatMode="all"
        onCycleRepeat={vi.fn()}
      />
    );
    expect(screen.getByLabelText("1曲リピートにする")).toHaveClass("playback-mode-btn--active");
  });
});
