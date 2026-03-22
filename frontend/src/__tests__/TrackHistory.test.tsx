import { render, screen, fireEvent, cleanup, waitFor } from "@testing-library/react";
import { describe, it, expect, afterEach, vi } from "vitest";
import { TrackHistory } from "../components/TrackHistory";

afterEach(cleanup);

// Mock API client — factory must be self-contained (vi.mock is hoisted)
vi.mock("../api/client", () => ({
  getTracks: vi.fn().mockResolvedValue({
    tracks: [
      {
        id: "t1",
        caption: "テストトラック1",
        title: "星空のメロディ",
        lyrics: "[Verse 1]\n夜空に浮かぶ星たちが\n僕らを照らしている",
        duration_ms: 180000,
        bpm: 120,
        music_key: "C",
        instrumental: false,
        play_count: 5,
        like_count: 2,
        created_at: "2026-03-21T10:00:00Z",
      },
      {
        id: "t2",
        caption: "テストトラック2",
        title: "風の通り道",
        duration_ms: 150000,
        bpm: 90,
        music_key: "Am",
        instrumental: true,
        play_count: 3,
        like_count: 0,
        created_at: "2026-03-21T11:00:00Z",
      },
    ],
    total: 2,
  }),
  getReaction: vi.fn().mockResolvedValue({ count: 2, user_reacted: false }),
  addReaction: vi.fn().mockResolvedValue({ ok: true, count: 3 }),
  removeReaction: vi.fn().mockResolvedValue({ ok: true, count: 1 }),
}));

describe("TrackHistory", () => {
  it("renders track titles", async () => {
    render(<TrackHistory channelSlug="anime" />);
    expect(await screen.findByText("星空のメロディ")).toBeInTheDocument();
    expect(screen.getByText("風の通り道")).toBeInTheDocument();
  });

  it("shows ReactionButton for each track", async () => {
    render(<TrackHistory channelSlug="anime" />);
    await screen.findByText("星空のメロディ");
    const buttons = screen.getAllByLabelText("いいね");
    expect(buttons.length).toBe(2);
  });

  it("shows expand icon for tracks with lyrics", async () => {
    render(<TrackHistory channelSlug="anime" />);
    await screen.findByText("星空のメロディ");
    // Track with lyrics should have expand indicator
    expect(screen.getByText("▶")).toBeInTheDocument();
  });

  it("does not show expand icon for tracks without lyrics", async () => {
    render(<TrackHistory channelSlug="anime" />);
    await screen.findByText("風の通り道");
    // Only one expand indicator (for track with lyrics)
    const indicators = screen.queryAllByText("▶");
    expect(indicators.length).toBe(1);
  });

  it("expands lyrics on track click", async () => {
    render(<TrackHistory channelSlug="anime" />);
    await screen.findByText("星空のメロディ");

    // Click track with lyrics
    fireEvent.click(screen.getByText("星空のメロディ"));

    await waitFor(() => {
      expect(screen.getByText("▼")).toBeInTheDocument();
      expect(screen.getByText("歌詞")).toBeInTheDocument();
    });
  });

  it("collapses lyrics on second click", async () => {
    render(<TrackHistory channelSlug="anime" />);
    await screen.findByText("星空のメロディ");

    // Expand
    fireEvent.click(screen.getByText("星空のメロディ"));
    await waitFor(() => {
      expect(screen.getByText("▼")).toBeInTheDocument();
    });

    // Collapse
    fireEvent.click(screen.getByText("星空のメロディ"));
    await waitFor(() => {
      expect(screen.getByText("▶")).toBeInTheDocument();
      expect(screen.queryByText("歌詞")).toBeNull();
    });
  });

  it("shows play count", async () => {
    render(<TrackHistory channelSlug="anime" />);
    await screen.findByText("星空のメロディ");
    expect(screen.getByText("5回再生")).toBeInTheDocument();
    expect(screen.getByText("3回再生")).toBeInTheDocument();
  });
});
