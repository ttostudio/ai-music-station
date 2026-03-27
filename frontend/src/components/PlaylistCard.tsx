import { Play, ListVideo } from "lucide-react";
import type { Playlist } from "../api/types";

interface Props {
  playlist: Playlist;
  onClick: () => void;
  onPlay: (e: React.MouseEvent) => void;
}

function formatDate(iso: string): string {
  const d = new Date(iso);
  return `${d.getMonth() + 1}/${d.getDate()}`;
}

export function PlaylistCard({ playlist, onClick, onPlay }: Props) {
  return (
    <div
      className="playlist-card"
      role="button"
      aria-label={`${playlist.name}を開く`}
      tabIndex={0}
      onClick={onClick}
      onKeyDown={(e) => e.key === "Enter" && onClick()}
    >
      <div className="playlist-card-icon">
        <ListVideo size={24} />
      </div>
      <div className="playlist-card-info">
        <div className="playlist-card-name">{playlist.name}</div>
        <div className="playlist-card-meta">
          {playlist.track_count}曲 · 最終更新 {formatDate(playlist.updated_at)}
        </div>
        {playlist.description && (
          <div className="playlist-card-desc">{playlist.description}</div>
        )}
      </div>
      <button
        className="playlist-card-play"
        aria-label={`${playlist.name}を再生`}
        onClick={onPlay}
      >
        <Play size={18} fill="currentColor" />
      </button>
    </div>
  );
}
