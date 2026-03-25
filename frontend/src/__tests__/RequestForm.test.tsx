import { render, screen, cleanup } from "@testing-library/react";
import { describe, it, expect, afterEach, vi } from "vitest";
import { RequestForm } from "../components/RequestForm";
import type { Channel } from "../api/types";

afterEach(cleanup);

vi.mock("../api/client", () => ({
  submitGenerate: vi.fn().mockResolvedValue({
    id: "req-1",
    channel_slug: "lofi",
    status: "pending",
    position: 1,
    created_at: "2026-03-25T00:00:00Z",
  }),
  getGenerateStatus: vi.fn().mockResolvedValue({
    id: "req-1",
    channel_slug: "lofi",
    status: "pending",
    mood: null,
    caption: null,
    lyrics: null,
    bpm: null,
    duration: null,
    music_key: null,
    position: 1,
    created_at: "2026-03-25T00:00:00Z",
    started_at: null,
    completed_at: null,
    error_message: null,
    track: null,
  }),
}));

const mockChannels: Channel[] = [
  {
    id: "1",
    slug: "lofi",
    name: "LoFi ビーツ",
    description: null,
    is_active: true,
    queue_depth: 0,
    total_tracks: 10,
    stream_url: "/stream/lofi",
    now_playing: null,
  },
  {
    id: "2",
    slug: "anime",
    name: "アニソン",
    description: null,
    is_active: true,
    queue_depth: 0,
    total_tracks: 5,
    stream_url: "/stream/anime",
    now_playing: null,
  },
];

describe("RequestForm", () => {
  it("renders channel selector", () => {
    render(<RequestForm channels={mockChannels} />);
    expect(screen.getByRole("combobox")).toBeInTheDocument();
    expect(screen.getByText("LoFi ビーツ")).toBeInTheDocument();
    expect(screen.getByText("アニソン")).toBeInTheDocument();
  });

  it("renders mood pills", () => {
    render(<RequestForm channels={mockChannels} />);
    expect(screen.getByText("明るい")).toBeInTheDocument();
    expect(screen.getByText("落ち着いた")).toBeInTheDocument();
    expect(screen.getByText("エネルギッシュ")).toBeInTheDocument();
    expect(screen.getByText("哀愁")).toBeInTheDocument();
  });

  it("renders prompt textarea", () => {
    render(<RequestForm channels={mockChannels} />);
    expect(screen.getByPlaceholderText(/追加の指示/)).toBeInTheDocument();
  });

  it("renders submit button", () => {
    render(<RequestForm channels={mockChannels} />);
    expect(screen.getByText("リクエスト送信")).toBeInTheDocument();
  });

  it("submit button is enabled when channel is selected", () => {
    render(<RequestForm channels={mockChannels} />);
    expect(screen.getByText("リクエスト送信")).not.toBeDisabled();
  });

  it("uses defaultSlug to pre-select channel", () => {
    render(<RequestForm channels={mockChannels} defaultSlug="anime" />);
    const select = screen.getByRole("combobox") as HTMLSelectElement;
    expect(select.value).toBe("anime");
  });
});
