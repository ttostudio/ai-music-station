import { render, screen, cleanup } from "@testing-library/react";
import { describe, it, expect, afterEach, beforeEach, vi } from "vitest";
import App from "../App";

beforeEach(() => {
  vi.stubGlobal("fetch", vi.fn().mockResolvedValue({
    ok: true,
    json: () => Promise.resolve({ channels: [], track: null, started_at: null }),
  }));
  vi.stubGlobal("AudioContext", vi.fn().mockImplementation(() => ({
    state: "running",
    resume: vi.fn().mockResolvedValue(undefined),
    createMediaElementSource: vi.fn().mockReturnValue({ connect: vi.fn() }),
    createAnalyser: vi.fn().mockReturnValue({
      connect: vi.fn(), disconnect: vi.fn(), fftSize: 2048,
      smoothingTimeConstant: 0.8, frequencyBinCount: 1024,
      getByteFrequencyData: vi.fn(),
    }),
    destination: {},
  })));
});

afterEach(() => { cleanup(); vi.restoreAllMocks(); });

describe("App", () => {
  it("renders loading state initially", () => {
    render(<App />);
    expect(
      screen.getAllByText("チャンネルを読み込み中...").length,
    ).toBeGreaterThan(0);
  });
});
