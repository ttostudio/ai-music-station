import { render, screen, cleanup } from "@testing-library/react";
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

  it("renders lyrics overlay when lyrics provided", () => {
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
