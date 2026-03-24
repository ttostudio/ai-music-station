import { AudioVisualizer } from "./AudioVisualizer";
import { KaraokeOverlay } from "./KaraokeOverlay";

interface Props {
  audioRef: React.RefObject<HTMLAudioElement | null>;
  isPlaying: boolean;
  channelSlug: string | null;
  lyrics?: string | null;
  elapsedMs: number;
  durationMs: number;
}

export function TheaterView({ audioRef, isPlaying, channelSlug, lyrics, elapsedMs, durationMs }: Props) {
  const hasLyrics = Boolean(lyrics && lyrics.trim());

  return (
    <div className="theater-view">
      <div className="theater-canvas-area">
        <AudioVisualizer audioRef={audioRef} isPlaying={isPlaying} channelSlug={channelSlug} />
      </div>

      {hasLyrics && (
        <div className="theater-karaoke">
          <KaraokeOverlay lyrics={lyrics!} elapsedMs={elapsedMs} durationMs={durationMs} variant="desktop" />
        </div>
      )}

      {!hasLyrics && (
        <div className="theater-instrumental">
          ♪ インストゥルメンタル
        </div>
      )}
    </div>
  );
}
