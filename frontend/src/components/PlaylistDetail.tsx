import { useState, useEffect, useCallback } from "react";
import {
  DndContext,
  closestCenter,
  PointerSensor,
  useSensor,
  useSensors,
  type DragEndEvent,
} from "@dnd-kit/core";
import {
  SortableContext,
  verticalListSortingStrategy,
  arrayMove,
} from "@dnd-kit/sortable";
import {
  ChevronLeft,
  Play,
  Shuffle,
  Plus,
  Pencil,
  Trash2,
  ListVideo,
} from "lucide-react";
import type {
  PlaylistDetail as PlaylistDetailType,
  Track,
} from "../api/types";
import { PlaylistTrackItem } from "./PlaylistTrackItem";
import { PlaylistCreateModal } from "./PlaylistCreateModal";
import { TrackSelectModal } from "./TrackSelectModal";
import {
  getPlaylist,
  updatePlaylist,
  deletePlaylist,
  addTrackToPlaylist,
  removeTrackFromPlaylist,
  reorderPlaylistTracks,
} from "../api/playlists";

interface Props {
  playlistId: string;
  onBack: () => void;
  onDeleted: () => void;
  fetchAllTracks: () => Promise<Track[]>;
  onPlayPlaylist?: (tracks: Track[], startIndex?: number) => void;
  onPlayTrack?: (track: Track, queue: Track[]) => void;
  currentTrackId?: string | null;
}

function formatTotalDuration(
  tracks: PlaylistDetailType["tracks"],
): string {
  const totalMs = tracks.reduce(
    (acc, e) => acc + (e.track.duration_ms ?? 0),
    0,
  );
  const totalSec = Math.floor(totalMs / 1000);
  const h = Math.floor(totalSec / 3600);
  const m = Math.floor((totalSec % 3600) / 60);
  if (h > 0) return `${h}時間${m}分`;
  return `${m}分`;
}

export function PlaylistDetail({
  playlistId,
  onBack,
  onDeleted,
  fetchAllTracks,
  onPlayPlaylist,
  onPlayTrack,
  currentTrackId,
}: Props) {
  const [detail, setDetail] = useState<PlaylistDetailType | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showEditModal, setShowEditModal] = useState(false);
  const [showTrackModal, setShowTrackModal] = useState(false);

  const sensors = useSensors(useSensor(PointerSensor));

  const load = useCallback(() => {
    setLoading(true);
    getPlaylist(playlistId)
      .then((d) => {
        setDetail(d);
        setError(null);
      })
      .catch(() => setError("プレイリストの読み込みに失敗しました"))
      .finally(() => setLoading(false));
  }, [playlistId]);

  useEffect(() => {
    load();
  }, [load]);

  async function handleEdit(name: string, description: string) {
    if (!detail) return;
    const updated = await updatePlaylist(playlistId, { name, description });
    setDetail({ ...updated, tracks: detail.tracks });
  }

  async function handleDelete() {
    if (!detail) return;
    if (!window.confirm(`「${detail.name}」を削除しますか？`)) return;
    await deletePlaylist(playlistId);
    onDeleted();
  }

  async function handleAddTracks(trackIds: string[]) {
    for (const trackId of trackIds) {
      await addTrackToPlaylist(playlistId, trackId);
    }
    load();
  }

  async function handleRemoveTrack(trackId: string) {
    if (!detail) return;
    setDetail((prev) =>
      prev
        ? {
            ...prev,
            tracks: prev.tracks.filter((e) => e.track.id !== trackId),
          }
        : prev,
    );
    try {
      await removeTrackFromPlaylist(playlistId, trackId);
    } catch {
      load();
    }
  }

  async function handleDragEnd(event: DragEndEvent) {
    if (!detail) return;
    const { active, over } = event;
    if (!over || active.id === over.id) return;

    const oldIndex = detail.tracks.findIndex(
      (e) => e.track.id === active.id,
    );
    const newIndex = detail.tracks.findIndex(
      (e) => e.track.id === over.id,
    );
    if (oldIndex === -1 || newIndex === -1) return;

    const reordered = arrayMove(detail.tracks, oldIndex, newIndex).map(
      (e, i) => ({ ...e, position: i }),
    );
    setDetail({ ...detail, tracks: reordered });

    try {
      await reorderPlaylistTracks(playlistId, {
        track_ids: reordered.map((e) => e.track.id),
      });
    } catch {
      load();
    }
  }

  const handlePlayAll = () => {
    if (!detail || !onPlayPlaylist) return;
    const tracks = detail.tracks.map((e) => e.track as Track);
    onPlayPlaylist(tracks, 0);
  };

  const handleShufflePlay = () => {
    if (!detail || !onPlayPlaylist) return;
    const tracks = detail.tracks.map((e) => e.track as Track);
    const startIndex = Math.floor(Math.random() * tracks.length);
    onPlayPlaylist(tracks, startIndex);
  };

  const handlePlayTrack = (index: number) => {
    if (!detail || !onPlayTrack) return;
    const tracks = detail.tracks.map((e) => e.track as Track);
    onPlayTrack(tracks[index], tracks);
  };

  const existingTrackIds = new Set(
    detail?.tracks.map((e) => e.track.id) ?? [],
  );

  if (loading && !detail) {
    return (
      <div className="playlist-detail-screen">
        <div className="playlist-detail-loading">読み込み中...</div>
      </div>
    );
  }

  if (error && !detail) {
    return (
      <div className="playlist-detail-screen">
        <div className="playlist-detail-error">{error}</div>
      </div>
    );
  }

  if (!detail) return null;

  return (
    <div className="playlist-detail-screen">
      {/* Header */}
      <div className="playlist-detail-header">
        <button
          className="playlist-detail-back"
          onClick={onBack}
          aria-label="戻る"
        >
          <ChevronLeft size={20} />
          <span>戻る</span>
        </button>
        <div className="playlist-detail-actions">
          <button
            className="playlist-detail-action-btn"
            onClick={() => setShowEditModal(true)}
            aria-label="編集"
          >
            <Pencil size={16} />
          </button>
          <button
            className="playlist-detail-action-btn playlist-detail-action-delete"
            onClick={handleDelete}
            aria-label="プレイリストを削除"
          >
            <Trash2 size={16} />
          </button>
        </div>
      </div>

      <div className="playlist-detail-body">
        {/* Cover + info */}
        <div className="playlist-detail-cover-row">
          <div className="playlist-detail-cover">
            <ListVideo size={40} />
          </div>
          <div className="playlist-detail-meta">
            <h1 className="playlist-detail-name">{detail.name}</h1>
            <p className="playlist-detail-stats">
              {detail.tracks.length}曲 · {formatTotalDuration(detail.tracks)}
            </p>
            {detail.description && (
              <p className="playlist-detail-desc">{detail.description}</p>
            )}
          </div>
        </div>

        {/* Play buttons */}
        <div className="playlist-detail-play-row">
          <button
            className="playlist-play-btn"
            onClick={handlePlayAll}
            disabled={detail.tracks.length === 0 || !onPlayPlaylist}
          >
            <Play size={16} fill="currentColor" />
            すべて再生
          </button>
          <button
            className="playlist-shuffle-btn"
            onClick={handleShufflePlay}
            disabled={detail.tracks.length === 0 || !onPlayPlaylist}
          >
            <Shuffle size={16} />
            シャッフル
          </button>
        </div>

        {/* Track list */}
        <div className="playlist-tracks-section">
          <div className="playlist-tracks-header">
            <span className="playlist-tracks-title">トラックリスト</span>
            <button
              className="playlist-tracks-add-btn"
              onClick={() => setShowTrackModal(true)}
            >
              <Plus size={14} />
              追加
            </button>
          </div>

          {detail.tracks.length === 0 ? (
            <div className="playlist-tracks-empty">
              トラックがありません。「追加」ボタンから追加してください
            </div>
          ) : (
            <DndContext
              sensors={sensors}
              collisionDetection={closestCenter}
              onDragEnd={handleDragEnd}
            >
              <SortableContext
                items={detail.tracks.map((e) => e.track.id)}
                strategy={verticalListSortingStrategy}
              >
                {detail.tracks.map((entry, index) => (
                  <PlaylistTrackItem
                    key={entry.track.id}
                    entry={entry}
                    index={index}
                    onRemove={() => handleRemoveTrack(entry.track.id)}
                    onPlay={onPlayTrack ? () => handlePlayTrack(index) : undefined}
                    isActive={entry.track.id === currentTrackId}
                  />
                ))}
              </SortableContext>
            </DndContext>
          )}
        </div>
      </div>

      {showEditModal && (
        <PlaylistCreateModal
          playlist={detail}
          onSave={handleEdit}
          onClose={() => setShowEditModal(false)}
        />
      )}

      {showTrackModal && (
        <TrackSelectModal
          existingTrackIds={existingTrackIds}
          onAdd={handleAddTracks}
          onClose={() => setShowTrackModal(false)}
          fetchTracks={fetchAllTracks}
        />
      )}
    </div>
  );
}
