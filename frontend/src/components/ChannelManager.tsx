import { useState, useEffect, useCallback } from "react";
import type { ChannelCreateBody, ChannelFullResponse } from "../api/types";
import {
  createChannel,
  updateChannel,
  deleteChannel,
  getChannels,
} from "../api/client";
import { ChannelForm } from "./ChannelForm";
import { ConfirmDialog } from "./ConfirmDialog";

interface ChannelRow {
  slug: string;
  name: string;
  total_tracks: number;
  queue_depth: number;
  is_active: boolean;
}

interface ChannelManagerProps {
  onClose: () => void;
}

export function ChannelManager({ onClose }: ChannelManagerProps) {
  const [channels, setChannels] = useState<ChannelRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [mode, setMode] = useState<"list" | "create" | "edit">("list");
  const [editingChannel, setEditingChannel] =
    useState<ChannelFullResponse | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  const loadChannels = useCallback(async () => {
    setLoading(true);
    try {
      const res = await getChannels();
      setChannels(
        res.channels.map((c) => ({
          slug: c.slug,
          name: c.name,
          total_tracks: c.total_tracks,
          queue_depth: c.queue_depth,
          is_active: c.is_active,
        })),
      );
    } catch {
      setMessage("チャンネル一覧の取得に失敗しました");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadChannels();
  }, [loadChannels]);

  async function handleCreate(body: ChannelCreateBody) {
    await createChannel(body);
    setMessage("チャンネルを作成しました");
    setMode("list");
    await loadChannels();
  }

  async function handleEdit(slug: string) {
    // Fetch full channel details via the detail endpoint
    const res = await fetch(`/api/channels/${slug}`);
    if (!res.ok) {
      setMessage("チャンネル情報の取得に失敗しました");
      return;
    }
    const detail = await res.json();
    // Map detail to ChannelFullResponse shape (detail endpoint may not have all fields)
    setEditingChannel({
      id: detail.id,
      slug: detail.slug,
      name: detail.name,
      description: detail.description ?? null,
      mood_description: detail.mood_description ?? null,
      is_active: detail.is_active,
      default_bpm_min: detail.default_bpm_min,
      default_bpm_max: detail.default_bpm_max,
      default_duration: detail.default_duration,
      default_key: detail.default_key ?? null,
      default_instrumental: detail.default_instrumental,
      prompt_template: detail.prompt_template ?? "",
      vocal_language: detail.vocal_language ?? null,
      auto_generate: detail.auto_generate ?? true,
      min_stock: detail.min_stock ?? 5,
      max_stock: detail.max_stock ?? 50,
    });
    setMode("edit");
  }

  async function handleUpdate(body: ChannelCreateBody) {
    if (!editingChannel) return;
    await updateChannel(editingChannel.slug, body);
    setMessage("チャンネルを更新しました");
    setMode("list");
    setEditingChannel(null);
    await loadChannels();
  }

  async function handleDelete() {
    if (!deleteTarget) return;
    try {
      const result = await deleteChannel(deleteTarget);
      setMessage(
        `チャンネルを削除しました（${result.deleted_tracks}件のトラックをアーカイブ）`,
      );
      setDeleteTarget(null);
      await loadChannels();
    } catch {
      setMessage("削除に失敗しました");
      setDeleteTarget(null);
    }
  }

  return (
    <div className="bg-gray-800 rounded-lg p-4 space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold text-white">チャンネル管理</h2>
        <button
          onClick={onClose}
          className="text-gray-400 hover:text-white text-lg"
        >
          ✕
        </button>
      </div>

      {message && (
        <div className="bg-gray-700 text-green-300 px-3 py-2 rounded text-sm">
          {message}
          <button
            onClick={() => setMessage(null)}
            className="ml-2 text-gray-400 hover:text-white"
          >
            ✕
          </button>
        </div>
      )}

      {mode === "list" && (
        <>
          <button
            onClick={() => setMode("create")}
            className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-500"
          >
            新規チャンネル作成
          </button>

          {loading ? (
            <p className="text-gray-400">読み込み中...</p>
          ) : channels.length === 0 ? (
            <p className="text-gray-400">チャンネルがありません</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm text-left">
                <thead className="text-gray-400 border-b border-gray-700">
                  <tr>
                    <th className="py-2 px-2">名前</th>
                    <th className="py-2 px-2">スラッグ</th>
                    <th className="py-2 px-2">トラック数</th>
                    <th className="py-2 px-2">待ち</th>
                    <th className="py-2 px-2">操作</th>
                  </tr>
                </thead>
                <tbody>
                  {channels.map((ch) => (
                    <tr
                      key={ch.slug}
                      className="border-b border-gray-700 text-gray-200"
                    >
                      <td className="py-2 px-2">{ch.name}</td>
                      <td className="py-2 px-2 font-mono text-gray-400">
                        {ch.slug}
                      </td>
                      <td className="py-2 px-2">{ch.total_tracks}</td>
                      <td className="py-2 px-2">{ch.queue_depth}</td>
                      <td className="py-2 px-2 space-x-2">
                        <button
                          onClick={() => handleEdit(ch.slug)}
                          className="text-blue-400 hover:text-blue-300"
                        >
                          編集
                        </button>
                        <button
                          onClick={() => setDeleteTarget(ch.slug)}
                          className="text-red-400 hover:text-red-300"
                        >
                          削除
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </>
      )}

      {mode === "create" && (
        <ChannelForm
          onSubmit={handleCreate}
          onCancel={() => setMode("list")}
        />
      )}

      {mode === "edit" && editingChannel && (
        <ChannelForm
          channel={editingChannel}
          onSubmit={handleUpdate}
          onCancel={() => {
            setMode("list");
            setEditingChannel(null);
          }}
        />
      )}

      <ConfirmDialog
        open={!!deleteTarget}
        title="チャンネル削除"
        message="このチャンネルを削除しますか？関連トラックは保持されます。"
        onConfirm={handleDelete}
        onCancel={() => setDeleteTarget(null)}
      />
    </div>
  );
}
