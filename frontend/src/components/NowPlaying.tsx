import type { Track } from "../api/types";
import { ReactionButton } from "./ReactionButton";

interface Props {
  track: Track | null;
  activeSlug?: string | null;
}

function getChannelGradientClass(slug: string | null | undefined): string {
  if (!slug) return "from-indigo-600 via-purple-600 to-pink-600";
  if (slug.includes("lofi") || slug.includes("lo-fi")) return "from-violet-600 via-purple-600 to-fuchsia-600";
  if (slug.includes("anime")) return "from-pink-600 via-rose-500 to-fuchsia-500";
  if (slug.includes("jazz")) return "from-amber-600 via-yellow-500 to-orange-500";
  if (slug.includes("game")) return "from-emerald-600 via-teal-500 to-green-500";
  return "from-indigo-600 via-purple-600 to-pink-600";
}

export function NowPlaying({ track, activeSlug }: Props) {
  if (!track) {
    return (
      <div className="text-center py-8" style={{ color: "var(--text-muted)" }}>
        チャンネルを選択して再生を開始してください
      </div>
    );
  }

  const gradientClass = getChannelGradientClass(activeSlug);

  return (
    <div className="glass-card p-5 relative overflow-hidden slide-up">
      {/* 動的チャンネルグラデーション背景 */}
      <div className={`absolute inset-0 opacity-10 bg-gradient-to-br ${gradientClass}`} />

      <div className="relative z-10 flex items-start justify-between">
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2 mb-2">
            {/* glow-pulse インジケーター */}
            <span
              className="inline-block w-2 h-2 rounded-full bg-green-400 glow-pulse"
              aria-hidden="true"
            />
            <span className="text-xs uppercase tracking-widest" style={{ color: "var(--text-secondary)" }}>
              再生中
            </span>
          </div>
          <div className="text-lg font-bold truncate">{track.title || track.caption}</div>

          {/* stagger入場アニメーション付きバッジ */}
          <div className="flex gap-3 mt-2 text-sm flex-wrap stagger-fade-in">
            {track.bpm && (
              <span className="badge-neo inline-flex items-center gap-1 text-sm" style={{ color: "var(--text-secondary)" }}>
                {track.bpm} BPM
              </span>
            )}
            {track.music_key && (
              <span className="badge-neo inline-flex items-center gap-1 text-sm" style={{ color: "var(--text-secondary)" }}>
                キー: {track.music_key}
              </span>
            )}
            {track.duration_ms && (
              <span className="badge-neo inline-flex items-center gap-1 text-sm" style={{ color: "var(--text-secondary)" }}>
                {Math.round(track.duration_ms / 1000)}秒
              </span>
            )}
            {track.instrumental !== null && (
              <span className="badge-neo inline-flex items-center gap-1 text-sm" style={{ color: "var(--text-secondary)" }}>
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
