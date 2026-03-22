import { render, screen, cleanup } from "@testing-library/react";
import { describe, it, expect, afterEach, vi, beforeEach } from "vitest";
import { createRef } from "react";
import { AudioVisualizer } from "../components/AudioVisualizer";

afterEach(cleanup);

// Mock AudioContext (jsdom does not implement Web Audio API)
const mockAnalyserConnect = vi.fn();
const mockAnalyserDisconnect = vi.fn();
const mockSourceConnect = vi.fn();
const mockAnalyser = {
  fftSize: 0,
  smoothingTimeConstant: 0,
  frequencyBinCount: 64,
  connect: mockAnalyserConnect,
  disconnect: mockAnalyserDisconnect,
  getByteFrequencyData: vi.fn(),
};
const mockSource = {
  connect: mockSourceConnect,
};
const mockCtx = {
  state: "running",
  createAnalyser: vi.fn().mockReturnValue(mockAnalyser),
  createMediaElementSource: vi.fn().mockReturnValue(mockSource),
  destination: {},
  close: vi.fn(),
};

beforeEach(() => {
  vi.stubGlobal("AudioContext", vi.fn().mockImplementation(() => mockCtx));
  vi.stubGlobal("cancelAnimationFrame", vi.fn());
  vi.stubGlobal("requestAnimationFrame", vi.fn().mockReturnValue(1));
  // Mock ResizeObserver
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

describe("AudioVisualizer", () => {
  it("renders canvas element", () => {
    const audioRef = createRef<HTMLAudioElement>();
    render(
      <AudioVisualizer
        audioRef={audioRef}
        isPlaying={false}
        channelSlug="lofi"
      />,
    );
    const canvas = document.querySelector("canvas");
    expect(canvas).toBeInTheDocument();
  });

  it("has correct role and aria-label", () => {
    const audioRef = createRef<HTMLAudioElement>();
    render(
      <AudioVisualizer
        audioRef={audioRef}
        isPlaying={false}
        channelSlug="lofi"
      />,
    );
    expect(screen.getByRole("img", { name: "オーディオビジュアライザー" })).toBeInTheDocument();
  });

  it("renders without error when channelSlug is null", () => {
    const audioRef = createRef<HTMLAudioElement>();
    render(
      <AudioVisualizer
        audioRef={audioRef}
        isPlaying={false}
        channelSlug={null}
      />,
    );
    expect(document.querySelector("canvas")).toBeInTheDocument();
  });

  it("renders without error when isPlaying is true", () => {
    const audioRef = createRef<HTMLAudioElement>();
    render(
      <AudioVisualizer
        audioRef={audioRef}
        isPlaying={true}
        channelSlug="anime"
      />,
    );
    expect(document.querySelector("canvas")).toBeInTheDocument();
  });
});
