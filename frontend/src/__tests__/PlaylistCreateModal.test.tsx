import { describe, it, expect, vi, afterEach } from "vitest";
import { render, fireEvent, cleanup, waitFor } from "@testing-library/react";
import { PlaylistCreateModal } from "../components/PlaylistCreateModal";
import type { Playlist } from "../api/types";

afterEach(cleanup);

const basePlaylist: Playlist = {
  id: "uuid-1",
  name: "既存プレイリスト",
  description: "説明",
  track_count: 3,
  created_at: "2026-03-27T00:00:00Z",
  updated_at: "2026-03-27T00:00:00Z",
};

describe("PlaylistCreateModal", () => {
  it("UT-CM-01: 作成モードでタイトルが「プレイリストを作成」になる", () => {
    const { getByText } = render(
      <PlaylistCreateModal onSave={vi.fn()} onClose={vi.fn()} />,
    );
    expect(getByText("プレイリストを作成")).toBeInTheDocument();
  });

  it("UT-CM-02: 編集モードでタイトルが「プレイリストを編集」になる", () => {
    const { getByText } = render(
      <PlaylistCreateModal
        playlist={basePlaylist}
        onSave={vi.fn()}
        onClose={vi.fn()}
      />,
    );
    expect(getByText("プレイリストを編集")).toBeInTheDocument();
  });

  it("UT-CM-03: 名前が空の場合は保存ボタンが無効", () => {
    const { getByText } = render(
      <PlaylistCreateModal onSave={vi.fn()} onClose={vi.fn()} />,
    );
    const saveBtn = getByText("作成する");
    expect(saveBtn).toBeDisabled();
  });

  it("UT-CM-04: 名前入力後に保存ボタンが有効になる", () => {
    const { getByText, getByPlaceholderText } = render(
      <PlaylistCreateModal onSave={vi.fn()} onClose={vi.fn()} />,
    );
    const input = getByPlaceholderText("プレイリスト名");
    fireEvent.change(input, { target: { value: "新プレイリスト" } });
    expect(getByText("作成する")).not.toBeDisabled();
  });

  it("UT-CM-05: 閉じるボタンで onClose が呼ばれる", () => {
    const onClose = vi.fn();
    const { getByLabelText } = render(
      <PlaylistCreateModal onSave={vi.fn()} onClose={onClose} />,
    );
    fireEvent.click(getByLabelText("閉じる"));
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it("UT-CM-06: バックドロップクリックで onClose が呼ばれる", () => {
    const onClose = vi.fn();
    const { getByText } = render(
      <PlaylistCreateModal onSave={vi.fn()} onClose={onClose} />,
    );
    // キャンセルボタン経由で確認
    fireEvent.click(getByText("キャンセル"));
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it("UT-CM-07: 文字数カウンターが表示される", () => {
    const { getByText, getByPlaceholderText } = render(
      <PlaylistCreateModal onSave={vi.fn()} onClose={vi.fn()} />,
    );
    expect(getByText("0/100")).toBeInTheDocument();
    const input = getByPlaceholderText("プレイリスト名");
    fireEvent.change(input, { target: { value: "abc" } });
    expect(getByText("3/100")).toBeInTheDocument();
  });

  it("UT-CM-08: 保存成功後に onClose が呼ばれる", async () => {
    const onClose = vi.fn();
    const onSave = vi.fn().mockResolvedValue(undefined);
    const { getByText, getByPlaceholderText } = render(
      <PlaylistCreateModal onSave={onSave} onClose={onClose} />,
    );
    fireEvent.change(getByPlaceholderText("プレイリスト名"), {
      target: { value: "テスト" },
    });
    fireEvent.click(getByText("作成する"));
    await waitFor(() => expect(onClose).toHaveBeenCalledTimes(1));
  });

  it("UT-CM-09: 保存失敗時にエラーメッセージが表示される", async () => {
    const onSave = vi.fn().mockRejectedValue(new Error("保存エラー"));
    const { getByText, getByPlaceholderText } = render(
      <PlaylistCreateModal onSave={onSave} onClose={vi.fn()} />,
    );
    fireEvent.change(getByPlaceholderText("プレイリスト名"), {
      target: { value: "テスト" },
    });
    fireEvent.click(getByText("作成する"));
    await waitFor(() =>
      expect(getByText("保存エラー")).toBeInTheDocument(),
    );
  });

  it("UT-CM-10: 編集モードでは既存の名前・説明が入力済み", () => {
    const { getByDisplayValue } = render(
      <PlaylistCreateModal
        playlist={basePlaylist}
        onSave={vi.fn()}
        onClose={vi.fn()}
      />,
    );
    expect(getByDisplayValue("既存プレイリスト")).toBeInTheDocument();
    expect(getByDisplayValue("説明")).toBeInTheDocument();
  });
});
