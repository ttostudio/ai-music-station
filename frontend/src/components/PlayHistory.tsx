import { Trash2 } from "lucide-react";
import type { Track } from "../api/types";
import type { HistoryEntry } from "../hooks/usePlayHistory";

interface Props {
  history: HistoryEntry[];
  onPlayTrack: (track: Track) => void;
  onClear: () => void;
}

function formatPlayedAt(isoString: string): string {
  const date = new Date(isoString);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMin = Math.floor(diffMs / 60000);
  if (diffMin < 1) return "たった今";
  if (diffMin < 60) return `${diffMin}分前`;
  const diffHour = Math.floor(diffMin / 60);
  if (diffHour < 24) return `${diffHour}時間前`;
  const diffDay = Math.floor(diffHour / 24);
  return `${diffDay}日前`;
}

export function PlayHistory({ history, onPlayTrack, onClear }: Props) {
  if (history.length === 0) {
    return (
      <div className="play-history-empty">
        再生履歴がありません
      </div>
    );
  }

  return (
    <div className="play-history">
      <div className="play-history-header">
        <span className="play-history-title">再生履歴</span>
        <button
          className="play-history-clear-btn"
          onClick={onClear}
          aria-label="再生履歴をクリア"
        >
          <Trash2 size={14} />
          <span>クリア</span>
        </button>
      </div>
      <ul className="play-history-list" aria-label="再生履歴">
        {history.map((entry) => {
          const title = entry.track.title || entry.track.caption;
          return (
            <li key={`${entry.track.id}-${entry.playedAt}`} className="play-history-item">
              <button
                className="play-history-item-btn"
                onClick={() => onPlayTrack(entry.track)}
                aria-label={`${title}を再生`}
              >
                <div className="play-history-item-info">
                  <span className="play-history-item-title">{title}</span>
                  {entry.track.mood && (
                    <span className="play-history-item-mood">{entry.track.mood}</span>
                  )}
                </div>
                <span className="play-history-item-time">{formatPlayedAt(entry.playedAt)}</span>
              </button>
            </li>
          );
        })}
      </ul>
    </div>
  );
}
