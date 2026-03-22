import type { Track } from "../api/types";
import { ReactionButton } from "./ReactionButton";

interface Props {
  track: Track | null;
  activeSlug?: string | null;
}

export function NowPlaying({ track }: Props) {
  if (!track) {
    return (
      <div className="text-center py-8" style={{ color: 'var(--text-muted)' }}>
        再生中のトラックはありません — リクエストを送信してください！
      </div>
    );
  }

  return (
    <div className="glass-card p-5 relative overflow-hidden">
      {/* Ambient background glow based on channel */}
      <div className="absolute inset-0 opacity-10 bg-gradient-to-br from-indigo-600 via-purple-600 to-pink-600" />

      <div className="relative z-10 flex items-start justify-between">
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2 mb-2">
            <span className="inline-block w-2 h-2 rounded-full bg-green-400 animate-pulse" />
            <span className="text-xs uppercase tracking-widest" style={{ color: 'var(--text-secondary)' }}>再生中</span>
          </div>
          <div className="text-lg font-bold truncate">{track.title || track.caption}</div>
          <div className="flex gap-4 mt-2 text-sm flex-wrap" style={{ color: 'var(--text-secondary)' }}>
            {track.bpm && (
              <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-white/5">
                {track.bpm} BPM
              </span>
            )}
            {track.music_key && (
              <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-white/5">
                キー: {track.music_key}
              </span>
            )}
            {track.duration_ms && (
              <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-white/5">
                {Math.round(track.duration_ms / 1000)}秒
              </span>
            )}
            {track.instrumental !== null && (
              <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-white/5">
                {track.instrumental ? "インスト" : "ボーカル"}
              </span>
            )}
          </div>
        </div>
        <ReactionButton trackId={track.id} />
      </div>
    </div>
  );
}
