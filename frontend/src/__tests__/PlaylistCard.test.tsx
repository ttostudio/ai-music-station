import { describe, it, expect, vi, afterEach } from "vitest";
import { render, fireEvent, cleanup } from "@testing-library/react";
import { PlaylistCard } from "../components/PlaylistCard";
import type { Playlist } from "../api/types";

afterEach(cleanup);

const playlist: Playlist = {
  id: "uuid-1",
  name: "テストプレイリスト",
  description: "説明テキスト",
  track_count: 5,
  created_at: "2026-03-27T00:00:00Z",
  updated_at: "2026-03-27T00:00:00Z",
};

describe("PlaylistCard", () => {
  it("UT-PC-01: プレイリスト名が表示される", () => {
    const { getByText } = render(
      <PlaylistCard
        playlist={playlist}
        onClick={vi.fn()}
        onPlay={vi.fn()}
      />,
    );
    expect(getByText("テストプレイリスト")).toBeInTheDocument();
  });

  it("UT-PC-02: トラック数とメタ情報が表示される", () => {
    const { getByText } = render(
      <PlaylistCard
        playlist={playlist}
        onClick={vi.fn()}
        onPlay={vi.fn()}
      />,
    );
    expect(getByText(/5曲/)).toBeInTheDocument();
  });

  it("UT-PC-03: カードクリックで onClick が呼ばれる", () => {
    const onClick = vi.fn();
    const { getByRole } = render(
      <PlaylistCard
        playlist={playlist}
        onClick={onClick}
        onPlay={vi.fn()}
      />,
    );
    fireEvent.click(getByRole("button", { name: /テストプレイリストを開く/ }));
    expect(onClick).toHaveBeenCalledTimes(1);
  });

  it("UT-PC-04: 再生ボタンクリックで onPlay が呼ばれる", () => {
    const onPlay = vi.fn();
    const { getByRole } = render(
      <PlaylistCard
        playlist={playlist}
        onClick={vi.fn()}
        onPlay={onPlay}
      />,
    );
    fireEvent.click(
      getByRole("button", { name: /テストプレイリストを再生/ }),
    );
    expect(onPlay).toHaveBeenCalledTimes(1);
  });

  it("UT-PC-05: description がある場合表示される", () => {
    const { getByText } = render(
      <PlaylistCard
        playlist={playlist}
        onClick={vi.fn()}
        onPlay={vi.fn()}
      />,
    );
    expect(getByText("説明テキスト")).toBeInTheDocument();
  });

  it("UT-PC-06: description が null の場合は説明欄が表示されない", () => {
    const noDesc = { ...playlist, description: null };
    const { queryByText } = render(
      <PlaylistCard
        playlist={noDesc}
        onClick={vi.fn()}
        onPlay={vi.fn()}
      />,
    );
    expect(queryByText("説明テキスト")).not.toBeInTheDocument();
  });

  it("UT-PC-07: aria-label にプレイリスト名が含まれる", () => {
    const { getByRole } = render(
      <PlaylistCard
        playlist={playlist}
        onClick={vi.fn()}
        onPlay={vi.fn()}
      />,
    );
    const card = getByRole("button", { name: /テストプレイリストを開く/ });
    expect(card).toHaveAttribute("aria-label", "テストプレイリストを開く");
  });

  it("UT-PC-08: Enterキーで onClick が呼ばれる", () => {
    const onClick = vi.fn();
    const { getByRole } = render(
      <PlaylistCard
        playlist={playlist}
        onClick={onClick}
        onPlay={vi.fn()}
      />,
    );
    const card = getByRole("button", { name: /テストプレイリストを開く/ });
    fireEvent.keyDown(card, { key: "Enter" });
    expect(onClick).toHaveBeenCalledTimes(1);
  });
});
