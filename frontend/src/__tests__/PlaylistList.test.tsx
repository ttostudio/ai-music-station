import { describe, it, expect, vi, afterEach, beforeEach } from "vitest";
import { render, fireEvent, cleanup, waitFor } from "@testing-library/react";
import { PlaylistList } from "../components/PlaylistList";
import type { Playlist } from "../api/types";

afterEach(cleanup);

vi.mock("../api/playlists", () => ({
  getPlaylists: vi.fn(),
  createPlaylist: vi.fn(),
}));

import { getPlaylists } from "../api/playlists";

const mockGetPlaylists = vi.mocked(getPlaylists);

const samplePlaylist: Playlist = {
  id: "uuid-1",
  name: "テストプレイリスト",
  description: "説明テキスト",
  track_count: 3,
  created_at: "2026-03-27T00:00:00Z",
  updated_at: "2026-03-27T00:00:00Z",
};

beforeEach(() => {
  vi.clearAllMocks();
});

describe("PlaylistList", () => {
  it("FE-001: プレイリスト一覧が表示される", async () => {
    mockGetPlaylists.mockResolvedValue({
      playlists: [samplePlaylist],
      total: 1,
      limit: 50,
      offset: 0,
    });

    const { getByText } = render(<PlaylistList onOpenDetail={vi.fn()} />);

    await waitFor(() =>
      expect(getByText("テストプレイリスト")).toBeInTheDocument(),
    );
  });

  it("FE-002: 空リスト時に空状態メッセージが表示される", async () => {
    mockGetPlaylists.mockResolvedValue({
      playlists: [],
      total: 0,
      limit: 50,
      offset: 0,
    });

    const { getByText } = render(<PlaylistList onOpenDetail={vi.fn()} />);

    await waitFor(() =>
      expect(getByText("プレイリストがありません")).toBeInTheDocument(),
    );
  });

  it("FE-003: 新規作成ボタンでモーダルが開く", async () => {
    mockGetPlaylists.mockResolvedValue({
      playlists: [],
      total: 0,
      limit: 50,
      offset: 0,
    });

    const { getByLabelText, getByText } = render(
      <PlaylistList onOpenDetail={vi.fn()} />,
    );

    await waitFor(() =>
      expect(getByText("プレイリストがありません")).toBeInTheDocument(),
    );

    fireEvent.click(getByLabelText("新しいプレイリストを作成"));
    expect(getByText("プレイリストを作成")).toBeInTheDocument();
  });

  it("FE-004: API エラー時にエラーメッセージが表示される", async () => {
    mockGetPlaylists.mockRejectedValue(new Error("network error"));

    const { getByText } = render(<PlaylistList onOpenDetail={vi.fn()} />);

    await waitFor(() =>
      expect(
        getByText("プレイリストの読み込みに失敗しました"),
      ).toBeInTheDocument(),
    );
  });
});
