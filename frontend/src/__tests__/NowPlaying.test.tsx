import { render, screen, cleanup } from "@testing-library/react";
import { describe, it, expect, afterEach } from "vitest";
import { NowPlaying } from "../components/NowPlaying";
import type { Track } from "../api/types";

afterEach(cleanup);

const mockTrack: Track = {
  id: "1",
  caption: "Rainy day lo-fi beat",
  duration_ms: 180000,
  bpm: 85,
  music_key: "Am",
  instrumental: true,
  play_count: 3,
  created_at: "2026-03-21T10:00:00Z",
};

describe("NowPlaying", () => {
  it("shows placeholder when no track", () => {
    render(<NowPlaying track={null} />);
    expect(screen.getAllByText(/No track playing/).length).toBeGreaterThan(0);
  });

  it("shows track caption", () => {
    render(<NowPlaying track={mockTrack} />);
    expect(
      screen.getAllByText("Rainy day lo-fi beat").length,
    ).toBeGreaterThan(0);
  });

  it("shows BPM", () => {
    render(<NowPlaying track={mockTrack} />);
    expect(screen.getAllByText("85 BPM").length).toBeGreaterThan(0);
  });

  it("shows key", () => {
    render(<NowPlaying track={mockTrack} />);
    expect(screen.getAllByText("Key: Am").length).toBeGreaterThan(0);
  });

  it("shows instrumental label", () => {
    render(<NowPlaying track={mockTrack} />);
    expect(screen.getAllByText("Instrumental").length).toBeGreaterThan(0);
  });
});
