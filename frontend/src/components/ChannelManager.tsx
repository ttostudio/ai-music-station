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
    const res = await fetch(`/api/channels/${slug}`);
    if (!res.ok) {
      setMessage("チャンネル情報の取得に失敗しました");
      return;
    }
    const detail = await res.json();
    setEditingChannel({
      id: detail.id,
      slug: detail.slug,
      name: detail.name,
      description: detail.description ?? null,
      mood_description: detail.mood_description ?? null,
      is_active: detail.is_active,
      default_bpm_min: detail.default_bpm_min,
      default_bpm_max: detail.default_bpm_max,
      min_duration: detail.min_duration,
      max_duration: detail.max_duration,
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
    <div className="glass-card p-5 space-y-4 slide-up">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold text-white">チャンネル管理</h2>
        <button
          onClick={onClose}
          className="w-8 h-8 rounded-full flex items-center justify-center text-gray-400 hover:text-white hover:bg-white/10 transition-all"
        >
          ✕
        </button>
      </div>

      {message && (
        <div className="px-4 py-2.5 rounded-lg text-sm bg-green-500/10 border border-green-500/20 text-green-400 flex items-center justify-between">
          <span>{message}</span>
          <button
            onClick={() => setMessage(null)}
            className="ml-2 text-green-400/60 hover:text-green-400"
          >
            ✕
          </button>
        </div>
      )}

      {mode === "list" && (
        <>
          <button
            onClick={() => setMode("create")}
            className="px-5 py-2.5 rounded-xl text-sm font-semibold text-white bg-gradient-to-r from-indigo-500 to-purple-600 hover:from-indigo-400 hover:to-purple-500 transition-all duration-300 hover:shadow-lg hover:shadow-indigo-500/25"
          >
            新規チャンネル作成
          </button>

          {loading ? (
            <p style={{ color: 'var(--text-secondary)' }}>読み込み中...</p>
          ) : channels.length === 0 ? (
            <p style={{ color: 'var(--text-secondary)' }}>チャンネルがありません</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm text-left">
                <thead className="border-b border-white/10">
                  <tr style={{ color: 'var(--text-secondary)' }}>
                    <th className="py-3 px-2 font-medium">名前</th>
                    <th className="py-3 px-2 font-medium">スラッグ</th>
                    <th className="py-3 px-2 font-medium">トラック数</th>
                    <th className="py-3 px-2 font-medium">待ち</th>
                    <th className="py-3 px-2 font-medium">操作</th>
                  </tr>
                </thead>
                <tbody>
                  {channels.map((ch) => (
                    <tr
                      key={ch.slug}
                      className="border-b border-white/5 text-gray-200 hover:bg-white/5 transition-colors"
                    >
                      <td className="py-3 px-2">{ch.name}</td>
                      <td className="py-3 px-2 font-mono text-xs" style={{ color: 'var(--text-secondary)' }}>
                        {ch.slug}
                      </td>
                      <td className="py-3 px-2">{ch.total_tracks}</td>
                      <td className="py-3 px-2">{ch.queue_depth}</td>
                      <td className="py-3 px-2 space-x-3">
                        <button
                          onClick={() => handleEdit(ch.slug)}
                          className="text-indigo-400 hover:text-indigo-300 transition-colors"
                        >
                          編集
                        </button>
                        <button
                          onClick={() => setDeleteTarget(ch.slug)}
                          className="text-red-400 hover:text-red-300 transition-colors"
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
