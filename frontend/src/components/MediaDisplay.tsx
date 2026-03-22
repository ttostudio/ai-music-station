import { useState } from "react";
import { AudioVisualizer } from "./AudioVisualizer";
import { LyricsDisplay } from "./LyricsDisplay";

type LyricsMode = "karaoke-overlay" | "scroll-panel";

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
  const [lyricsMode, setLyricsMode] = useState<LyricsMode>("karaoke-overlay");
  const hasLyrics = Boolean(lyrics && lyrics.trim());
  const isOverlayMode = lyricsMode === "karaoke-overlay";

  return (
    <div
      className={`media-display${isOverlayMode ? "" : " media-display-panel-mode"}`}
      aria-label={videoUrl ? "Music Video再生中" : undefined}
    >
      {/* ビジュアライザー層 */}
      <div className={isOverlayMode ? undefined : "media-visualizer-area"}>
        {/* 背景層 (z-index: 0) */}
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

        {/* カラオケオーバーレイ (z-index: 10) — Pattern B、歌詞あり時のみ */}
        {hasLyrics && isOverlayMode && (
          <LyricsDisplay
            lyrics={lyrics!}
            elapsedMs={elapsedMs}
            durationMs={durationMs}
            mode="karaoke-overlay"
            channelSlug={channelSlug}
          />
        )}
      </div>

      {/* スクロールパネル — Pattern A、歌詞あり時のみ */}
      {hasLyrics && !isOverlayMode && (
        <LyricsDisplay
          lyrics={lyrics!}
          elapsedMs={elapsedMs}
          durationMs={durationMs}
          mode="scroll-panel"
          channelSlug={channelSlug}
        />
      )}

      {/* 切替トグルボタン (z-index: 20) — 歌詞あり時のみ */}
      {hasLyrics && (
        <div className="lyrics-mode-toggle">
          <button
            className={`lyrics-mode-btn focus-ring${lyricsMode === "scroll-panel" ? " lyrics-mode-btn-active" : ""}`}
            onClick={() => setLyricsMode("scroll-panel")}
            aria-label="歌詞をテキストパネルで表示"
            aria-pressed={lyricsMode === "scroll-panel"}
          >
            ≡
          </button>
          <button
            className={`lyrics-mode-btn focus-ring${lyricsMode === "karaoke-overlay" ? " lyrics-mode-btn-active" : ""}`}
            onClick={() => setLyricsMode("karaoke-overlay")}
            aria-label="歌詞をカラオケオーバーレイで表示"
            aria-pressed={lyricsMode === "karaoke-overlay"}
          >
            ⊡
          </button>
        </div>
      )}
    </div>
  );
}
