import { useEffect, useState } from "react";
import { getTracks } from "../api/client";
import type { Track } from "../api/types";
import { ReactionButton } from "./ReactionButton";
import { LyricsDisplay } from "./LyricsDisplay";

interface Props {
  channelSlug: string;
}

export function TrackHistory({ channelSlug }: Props) {
  const [tracks, setTracks] = useState<Track[]>([]);
  const [expandedId, setExpandedId] = useState<string | null>(null);

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
      {tracks.map((track) => {
        const isExpanded = expandedId === track.id;
        return (
          <div key={track.id} className="glass-card-hover overflow-hidden">
            <div
              className={`px-4 py-3 text-sm flex items-center gap-3 ${track.lyrics ? "cursor-pointer" : ""}`}
              onClick={() => track.lyrics && setExpandedId(isExpanded ? null : track.id)}
            >
              {track.lyrics && (
                <span className="shrink-0 text-xs" style={{ color: 'var(--text-muted)' }}>
                  {isExpanded ? "▼" : "▶"}
                </span>
              )}
              <span className="truncate flex-1">{track.title || track.caption}</span>
              <span className="shrink-0 text-xs tabular-nums" style={{ color: 'var(--text-secondary)' }}>
                {track.play_count}回再生
              </span>
              <span onClick={(e) => e.stopPropagation()}>
                <ReactionButton trackId={track.id} />
              </span>
            </div>
            {isExpanded && track.lyrics && (
              <div className="px-4 pb-3">
                <LyricsDisplay lyrics={track.lyrics} elapsedMs={0} durationMs={0} />
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
