import { AudioVisualizer } from "./AudioVisualizer";
import { LyricsDisplay } from "./LyricsDisplay";

interface Props {
  audioRef: React.RefObject<HTMLAudioElement | null>;
  isPlaying: boolean;
  channelSlug: string | null;
  videoUrl?: string;
  // Phase 2拡張ポイント: videoUrl が存在する場合に <video> を背景層として使用
  lyrics?: string | null;
  elapsedMs: number;
  durationMs: number;
}

export function MediaDisplay({
  audioRef,
  isPlaying,
  channelSlug,
  videoUrl,
  lyrics,
  elapsedMs,
  durationMs,
}: Props) {
  return (
    <div className="media-display" aria-label={videoUrl ? "Music Video再生中" : undefined}>
      {/* 背景層 (z-index: 0) */}
      {/* Phase 2拡張ポイント: videoUrl がある場合は <video> に差し替え */}
      {videoUrl ? (
        <video
          className="absolute inset-0 w-full h-full object-cover"
          src={videoUrl}
          autoPlay
          loop
          muted
          playsInline
        />
      ) : (
        <AudioVisualizer
          audioRef={audioRef}
          isPlaying={isPlaying}
          channelSlug={channelSlug}
        />
      )}

      {/* 前景層: 歌詞オーバーレイ (z-index: 10) — 歌詞なし時は非表示 */}
      {lyrics && (
        <LyricsDisplay
          lyrics={lyrics}
          elapsedMs={elapsedMs}
          durationMs={durationMs}
          mode="karaoke-overlay"
          channelSlug={channelSlug}
        />
      )}
    </div>
  );
}
