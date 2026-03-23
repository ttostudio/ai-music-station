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

describe("MediaDisplay split view layout", () => {
  it("does not show lyrics views when no lyrics", () => {
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
    expect(document.querySelector(".lyrics-panel")).toBeNull();
  });

  it("shows both karaoke overlay and scroll panel when lyrics are provided", () => {
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
    expect(document.querySelector(".lyrics-panel")).toBeInTheDocument();
  });

  it("uses media-display-split class for split layout", () => {
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
    expect(mediaDisplay).toHaveClass("media-display-split");
  });

  it("renders karaoke overlay inside media-upper section", () => {
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
    const upper = document.querySelector(".media-upper");
    expect(upper).toBeInTheDocument();
    expect(upper?.querySelector(".karaoke-overlay")).toBeInTheDocument();
  });

  it("renders both views simultaneously without toggle", () => {
    const audioRef = createRef<HTMLAudioElement>();
    render(
      <MediaDisplay
        audioRef={audioRef}
        isPlaying={false}
        channelSlug="lofi"
        lyrics="星空に浮かぶ\n君の笑顔が"
        elapsedMs={5000}
        durationMs={120000}
      />,
    );
    // Both views coexist
    const overlays = document.querySelectorAll(".karaoke-overlay");
    const panels = document.querySelectorAll(".lyrics-panel");
    expect(overlays.length).toBe(1);
    expect(panels.length).toBe(1);
  });
});

// ===== インストゥルメンタル表示テスト =====

describe("MediaDisplay instrumental display", () => {
  it("shows instrumental label when no lyrics provided", () => {
    const audioRef = createRef<HTMLAudioElement>();
    render(
      <MediaDisplay
        audioRef={audioRef}
        isPlaying={false}
        channelSlug="lofi"
        elapsedMs={0}
        durationMs={180000}
      />,
    );
    expect(screen.getByText("♪ インストゥルメンタル")).toBeInTheDocument();
  });

  it("shows instrumental label when lyrics is empty string", () => {
    const audioRef = createRef<HTMLAudioElement>();
    render(
      <MediaDisplay
        audioRef={audioRef}
        isPlaying={false}
        channelSlug="lofi"
        lyrics=""
        elapsedMs={0}
        durationMs={180000}
      />,
    );
    expect(screen.getByText("♪ インストゥルメンタル")).toBeInTheDocument();
  });

  it("shows instrumental label when lyrics is whitespace only", () => {
    const audioRef = createRef<HTMLAudioElement>();
    render(
      <MediaDisplay
        audioRef={audioRef}
        isPlaying={false}
        channelSlug="lofi"
        lyrics="   "
        elapsedMs={0}
        durationMs={180000}
      />,
    );
    expect(screen.getByText("♪ インストゥルメンタル")).toBeInTheDocument();
  });

  it("does not show instrumental label when lyrics provided", () => {
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
    expect(screen.queryByText("♪ インストゥルメンタル")).toBeNull();
  });

  it("instrumental label has pointer-events none", () => {
    const audioRef = createRef<HTMLAudioElement>();
    render(
      <MediaDisplay
        audioRef={audioRef}
        isPlaying={false}
        channelSlug="lofi"
        elapsedMs={0}
        durationMs={180000}
      />,
    );
    const label = screen.getByText("♪ インストゥルメンタル");
    expect(label).toHaveStyle({ pointerEvents: "none" });
  });

  it("does not show lyrics mode toggle when no lyrics", () => {
    const audioRef = createRef<HTMLAudioElement>();
    render(
      <MediaDisplay
        audioRef={audioRef}
        isPlaying={false}
        channelSlug="lofi"
        elapsedMs={0}
        durationMs={180000}
      />,
    );
    expect(screen.queryByLabelText("歌詞をテキストパネルで表示")).toBeNull();
    expect(screen.queryByLabelText("歌詞をカラオケオーバーレイで表示")).toBeNull();
  });
});
