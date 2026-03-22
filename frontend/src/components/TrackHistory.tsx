import { useEffect, useState } from "react";
import { getTracks } from "../api/client";
import type { Track } from "../api/types";
import { ReactionButton } from "./ReactionButton";
import { LyricsDisplay } from "./LyricsDisplay";

interface Props {
  channelSlug: string;
  nowPlayingId?: string | null;
}

export function TrackHistory({ channelSlug, nowPlayingId }: Props) {
  const [tracks, setTracks] = useState<Track[]>([]);
  const [expandedId, setExpandedId] = useState<string | null>(null);

  useEffect(() => {
    getTracks(channelSlug, 10)
      .then((data) => setTracks(data.tracks))
      .catch(() => setTracks([]));
  }, [channelSlug]);

  if (tracks.length === 0) {
    return (
      <div className="text-sm text-center py-3" style={{ color: "var(--text-muted)" }}>
        このチャンネルにはまだトラックがありません。
      </div>
    );
  }

  return (
    <div className="space-y-2">
      <div className="text-sm font-semibold" style={{ color: "var(--text-primary)" }}>最近のトラック</div>
      <div className="space-y-2 track-list-animated">
      {tracks.map((track, idx) => {
        const isExpanded = expandedId === track.id;
        const isNowPlaying = nowPlayingId === track.id;
        return (
          <div
            key={track.id}
            className={`track-item glass-card-hover overflow-hidden ${isNowPlaying ? "border border-indigo-500/30" : ""}`}
            style={{
              animationDelay: `${idx * 50}ms`,
            }}
          >
            <div
              className={`px-4 py-3 text-sm flex items-center gap-3 ${track.lyrics ? "cursor-pointer" : ""}`}
              onClick={() => track.lyrics && setExpandedId(isExpanded ? null : track.id)}
            >
              {isNowPlaying && (
                <span className="shrink-0">
                  <span className="visualizer" style={{ height: "16px" }}>
                    {[0, 1, 2].map((i) => (
                      <span
                        key={i}
                        className="visualizer-bar"
                        style={{
                          width: "2px",
                          animationDelay: `${i * 0.15}s`,
                          ["--duration" as string]: `${0.5 + i * 0.1}s`,
                        }}
                      />
                    ))}
                  </span>
                </span>
              )}
              {!isNowPlaying && track.lyrics && (
                <span className={`shrink-0 text-xs expand-arrow ${isExpanded ? "expand-arrow-open" : ""}`} style={{ color: "var(--text-muted)" }}>
                  ▶
                </span>
              )}
              <span className={`truncate flex-1 ${isNowPlaying ? "font-semibold text-indigo-300" : ""}`}>
                {track.title || track.caption}
              </span>
              <span className="shrink-0 text-xs tabular-nums" style={{ color: "var(--text-secondary)" }}>
                {track.play_count}回再生
              </span>
              <span onClick={(e) => e.stopPropagation()}>
                <ReactionButton trackId={track.id} />
              </span>
            </div>

            {/* 展開歌詞 — 常時レンダリング、CSS max-height でトランジション */}
            {track.lyrics && (
              <div className={`expand-content ${isExpanded ? "expand-content-open" : ""}`}>
                <div className="px-4 pb-3">
                  <LyricsDisplay lyrics={track.lyrics} elapsedMs={0} durationMs={0} />
                </div>
              </div>
            )}
          </div>
        );
      })}
      </div>
    </div>
  );
}
