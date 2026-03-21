import { render, screen, cleanup } from "@testing-library/react";
import { describe, it, expect, afterEach } from "vitest";
import { TrackTitle } from "../components/TrackTitle";
import type { Track } from "../api/types";

afterEach(cleanup);

const baseTrack: Track = {
  id: "1",
  caption: "雨の日のローファイビート",
  duration_ms: 180000,
  bpm: 85,
  music_key: "Am",
  instrumental: false,
  play_count: 3,
  created_at: "2026-03-21T10:00:00Z",
};

describe("TrackTitle", () => {
  it("shows caption when no title", () => {
    render(<TrackTitle track={baseTrack} />);
    expect(
      screen.getByText("雨の日のローファイビート"),
    ).toBeInTheDocument();
  });

  it("shows title when provided", () => {
    render(<TrackTitle track={{ ...baseTrack, title: "夕暮れの散歩道" }} />);
    expect(screen.getByText("夕暮れの散歩道")).toBeInTheDocument();
  });

  it("shows mood when provided", () => {
    render(<TrackTitle track={{ ...baseTrack, mood: "ノスタルジック" }} />);
    expect(screen.getByText("ノスタルジック")).toBeInTheDocument();
  });

  it("shows instrumental label when instrumental", () => {
    render(<TrackTitle track={{ ...baseTrack, instrumental: true }} />);
    expect(screen.getByText("🎵 インスト楽曲")).toBeInTheDocument();
  });

  it("does not show instrumental label for vocal tracks", () => {
    render(<TrackTitle track={baseTrack} />);
    expect(screen.queryByText("🎵 インスト楽曲")).toBeNull();
  });
});
