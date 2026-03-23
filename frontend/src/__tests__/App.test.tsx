import { render, screen, cleanup } from "@testing-library/react";
import { describe, it, expect, afterEach, vi } from "vitest";

vi.mock("../hooks/useNowPlaying", () => ({
  useNowPlaying: () => ({ track: null, startedAt: null, elapsedMs: 0 }),
}));

vi.mock("../hooks/useChannels", () => ({
  useChannels: () => ({ channels: [], loading: true, error: null }),
}));

vi.mock("../components/AudioVisualizer", () => ({
  AudioVisualizer: () => null,
  resumeAudioContext: () => {},
}));

import App from "../App";

afterEach(cleanup);

describe("App", () => {
  it("renders loading state initially", () => {
    render(<App />);
    expect(
      screen.getAllByText("チャンネルを読み込み中...").length,
    ).toBeGreaterThan(0);
  });
});
