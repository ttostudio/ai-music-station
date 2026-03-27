import { useState, useEffect } from "react";
import { Plus, ListVideo } from "lucide-react";
import type { Playlist } from "../api/types";
import { PlaylistCard } from "./PlaylistCard";
import { PlaylistCreateModal } from "./PlaylistCreateModal";
import { getPlaylists, createPlaylist } from "../api/playlists";

interface Props {
  onOpenDetail: (id: string) => void;
}

export function PlaylistList({ onOpenDetail }: Props) {
  const [playlists, setPlaylists] = useState<Playlist[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showCreateModal, setShowCreateModal] = useState(false);

  function load() {
    setLoading(true);
    getPlaylists()
      .then((res) => {
        setPlaylists(res.playlists);
        setError(null);
      })
      .catch(() => setError("プレイリストの読み込みに失敗しました"))
      .finally(() => setLoading(false));
  }

  useEffect(() => {
    load();
  }, []);

  async function handleCreate(name: string, description: string) {
    const created = await createPlaylist({ name, description });
    setPlaylists((prev) => [created, ...prev]);
  }

  function handlePlay(e: React.MouseEvent, playlist: Playlist) {
    e.stopPropagation();
    onOpenDetail(playlist.id);
  }

  return (
    <div className="playlist-list-tab">
      <div className="playlist-list-header">
        <h1 className="playlist-list-title">マイプレイリスト</h1>
        <button
          className="playlist-list-add-btn"
          onClick={() => setShowCreateModal(true)}
          aria-label="新しいプレイリストを作成"
        >
          <Plus size={20} />
        </button>
      </div>

      {loading && (
        <div className="playlist-list-loading">読み込み中...</div>
      )}

      {error && <div className="playlist-list-error">{error}</div>}

      {!loading && !error && playlists.length === 0 && (
        <div className="playlist-empty-state">
          <ListVideo size={48} className="playlist-empty-icon" />
          <p className="playlist-empty-text">プレイリストがありません</p>
          <button
            className="playlist-empty-btn"
            onClick={() => setShowCreateModal(true)}
          >
            新しいプレイリストを作成
          </button>
        </div>
      )}

      {!loading && playlists.length > 0 && (
        <div className="playlist-cards">
          {playlists.map((pl) => (
            <PlaylistCard
              key={pl.id}
              playlist={pl}
              onClick={() => onOpenDetail(pl.id)}
              onPlay={(e) => handlePlay(e, pl)}
            />
          ))}
        </div>
      )}

      {showCreateModal && (
        <PlaylistCreateModal
          onSave={handleCreate}
          onClose={() => setShowCreateModal(false)}
        />
      )}
    </div>
  );
}
