import { render, screen, cleanup, fireEvent } from "@testing-library/react";
import { describe, it, expect, afterEach, vi, beforeEach } from "vitest";
import { createRef } from "react";
import { MediaDisplay } from "../components/MediaDisplay";

afterEach(cleanup);

beforeEach(() => {
  vi.stubGlobal("AudioContext", vi.fn().mockImplementation(() => ({
    state: "running",
    createAnalyser: vi.fn().mockReturnValue({
      fftSize: 0,
      smoothingTimeConstant: 0,
      frequencyBinCount: 64,
      connect: vi.fn(),
      disconnect: vi.fn(),
      getByteFrequencyData: vi.fn(),
    }),
    createMediaElementSource: vi.fn().mockReturnValue({ connect: vi.fn() }),
    destination: {},
  })));
  vi.stubGlobal("cancelAnimationFrame", vi.fn());
  vi.stubGlobal("requestAnimationFrame", vi.fn().mockReturnValue(1));
  vi.stubGlobal(
    "ResizeObserver",
    vi.fn().mockImplementation(() => ({
      observe: vi.fn(),
      disconnect: vi.fn(),
    })),
  );
});

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("MediaDisplay", () => {
  it("renders AudioVisualizer canvas when no videoUrl", () => {
    const audioRef = createRef<HTMLAudioElement>();
    render(
      <MediaDisplay
        audioRef={audioRef}
        isPlaying={false}
        channelSlug="lofi"
        elapsedMs={0}
        durationMs={0}
      />,
    );
    expect(document.querySelector("canvas")).toBeInTheDocument();
  });

  it("renders video element when videoUrl is provided", () => {
    const audioRef = createRef<HTMLAudioElement>();
    render(
      <MediaDisplay
        audioRef={audioRef}
        isPlaying={false}
        channelSlug="lofi"
        videoUrl="http://example.com/video.mp4"
        elapsedMs={0}
        durationMs={0}
      />,
    );
    expect(document.querySelector("video")).toBeInTheDocument();
  });

  it("does not render lyrics overlay when no lyrics", () => {
    const audioRef = createRef<HTMLAudioElement>();
    render(
      <MediaDisplay
        audioRef={audioRef}
        isPlaying={false}
        channelSlug="lofi"
        elapsedMs={0}
        durationMs={0}
      />,
    );
    expect(document.querySelector(".karaoke-overlay")).toBeNull();
  });

  it("renders karaoke overlay (Pattern B default) when lyrics provided", () => {
    const audioRef = createRef<HTMLAudioElement>();
    render(
      <MediaDisplay
        audioRef={audioRef}
        isPlaying={false}
        channelSlug="lofi"
        lyrics="星空に浮かぶ\n君の笑顔が"
        elapsedMs={0}
        durationMs={120000}
      />,
    );
    expect(document.querySelector(".karaoke-overlay")).toBeInTheDocument();
  });

  it("has correct aria-label when playing video", () => {
    const audioRef = createRef<HTMLAudioElement>();
    render(
      <MediaDisplay
        audioRef={audioRef}
        isPlaying={false}
        channelSlug="lofi"
        videoUrl="http://example.com/video.mp4"
        elapsedMs={0}
        durationMs={0}
      />,
    );
    expect(screen.getByLabelText("Music Video再生中")).toBeInTheDocument();
  });
});

describe("MediaDisplay lyrics mode toggle", () => {
  it("does not show toggle buttons when no lyrics", () => {
    const audioRef = createRef<HTMLAudioElement>();
    render(
      <MediaDisplay
        audioRef={audioRef}
        isPlaying={false}
        channelSlug="lofi"
        elapsedMs={0}
        durationMs={0}
      />,
    );
    expect(screen.queryByLabelText("歌詞をテキストパネルで表示")).toBeNull();
    expect(screen.queryByLabelText("歌詞をカラオケオーバーレイで表示")).toBeNull();
  });

  it("shows toggle buttons when lyrics are provided", () => {
    const audioRef = createRef<HTMLAudioElement>();
    render(
      <MediaDisplay
        audioRef={audioRef}
        isPlaying={false}
        channelSlug="lofi"
        lyrics="星空に浮かぶ\n君の笑顔が"
        elapsedMs={0}
        durationMs={120000}
      />,
    );
    expect(screen.getByLabelText("歌詞をテキストパネルで表示")).toBeInTheDocument();
    expect(screen.getByLabelText("歌詞をカラオケオーバーレイで表示")).toBeInTheDocument();
  });

  it("starts with karaoke-overlay (Pattern B) as default", () => {
    const audioRef = createRef<HTMLAudioElement>();
    render(
      <MediaDisplay
        audioRef={audioRef}
        isPlaying={false}
        channelSlug="lofi"
        lyrics="星空に浮かぶ\n君の笑顔が"
        elapsedMs={0}
        durationMs={120000}
      />,
    );
    const overlayBtn = screen.getByLabelText("歌詞をカラオケオーバーレイで表示");
    expect(overlayBtn).toHaveAttribute("aria-pressed", "true");
    const scrollBtn = screen.getByLabelText("歌詞をテキストパネルで表示");
    expect(scrollBtn).toHaveAttribute("aria-pressed", "false");
  });

  it("switches to scroll-panel (Pattern A) when scroll button is clicked", () => {
    const audioRef = createRef<HTMLAudioElement>();
    render(
      <MediaDisplay
        audioRef={audioRef}
        isPlaying={false}
        channelSlug="lofi"
        lyrics="星空に浮かぶ\n君の笑顔が"
        elapsedMs={0}
        durationMs={120000}
      />,
    );
    const scrollBtn = screen.getByLabelText("歌詞をテキストパネルで表示");
    fireEvent.click(scrollBtn);

    // karaoke overlay should be gone
    expect(document.querySelector(".karaoke-overlay")).toBeNull();
    // lyrics panel should appear
    expect(document.querySelector(".lyrics-panel")).toBeInTheDocument();
    // aria-pressed updated
    expect(scrollBtn).toHaveAttribute("aria-pressed", "true");
  });

  it("switches back to karaoke-overlay when overlay button is clicked", () => {
    const audioRef = createRef<HTMLAudioElement>();
    render(
      <MediaDisplay
        audioRef={audioRef}
        isPlaying={false}
        channelSlug="lofi"
        lyrics="星空に浮かぶ\n君の笑顔が"
        elapsedMs={0}
        durationMs={120000}
      />,
    );
    // Switch to scroll-panel first
    fireEvent.click(screen.getByLabelText("歌詞をテキストパネルで表示"));
    // Switch back to overlay
    fireEvent.click(screen.getByLabelText("歌詞をカラオケオーバーレイで表示"));

    expect(document.querySelector(".karaoke-overlay")).toBeInTheDocument();
    expect(document.querySelector(".lyrics-panel")).toBeNull();
  });

  it("applies media-display-panel-mode class in scroll-panel mode", () => {
    const audioRef = createRef<HTMLAudioElement>();
    const { container } = render(
      <MediaDisplay
        audioRef={audioRef}
        isPlaying={false}
        channelSlug="lofi"
        lyrics="星空に浮かぶ\n君の笑顔が"
        elapsedMs={0}
        durationMs={120000}
      />,
    );
    const mediaDisplay = container.querySelector(".media-display");
    expect(mediaDisplay).not.toHaveClass("media-display-panel-mode");

    fireEvent.click(screen.getByLabelText("歌詞をテキストパネルで表示"));
    expect(mediaDisplay).toHaveClass("media-display-panel-mode");
  });
});
