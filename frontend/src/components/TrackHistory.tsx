import { useEffect, useState } from "react";
import { getTracks } from "../api/client";
import type { Track } from "../api/types";

interface Props {
  channelSlug: string;
}

export function TrackHistory({ channelSlug }: Props) {
  const [tracks, setTracks] = useState<Track[]>([]);

  useEffect(() => {
    getTracks(channelSlug, 10)
      .then((data) => setTracks(data.tracks))
      .catch(() => setTracks([]));
  }, [channelSlug]);

  if (tracks.length === 0) {
    return (
      <div className="text-sm text-center py-3" style={{ color: 'var(--text-muted)' }}>
        このチャンネルにはまだトラックがありません。
      </div>
    );
  }

  return (
    <div className="space-y-2">
      <div className="text-sm font-semibold" style={{ color: 'var(--text-primary)' }}>最近のトラック</div>
      {tracks.map((track) => (
        <div
          key={track.id}
          className="glass-card-hover px-4 py-3 text-sm flex justify-between items-center"
        >
          <span className="truncate flex-1">{track.title || track.caption}</span>
          <span className="ml-3 shrink-0 text-xs tabular-nums" style={{ color: 'var(--text-secondary)' }}>
            👍{track.like_count ?? 0} / {track.play_count}回再生
          </span>
        </div>
      ))}
    </div>
  );
}
