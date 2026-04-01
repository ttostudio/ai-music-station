import { Play, Pause, SkipBack, SkipForward, Shuffle, Repeat, Repeat1 } from "lucide-react";
import type { RepeatMode } from "../hooks/usePlaylistPlayer";

interface Props {
  isPlaying: boolean;
  onPlayPause: () => void;
  onSkipPrev: () => void;
  onSkipNext: () => void;
  shuffle?: boolean;
  repeatMode?: RepeatMode;
  onToggleShuffle?: () => void;
  onCycleRepeat?: () => void;
}

export function PlaybackControls({
  isPlaying,
  onPlayPause,
  onSkipPrev,
  onSkipNext,
  shuffle,
  repeatMode,
  onToggleShuffle,
  onCycleRepeat,
}: Props) {
  return (
    <div className="playback-controls">
      {onToggleShuffle && (
        <button
          className={`playback-mode-btn${shuffle ? " playback-mode-btn--active" : ""}`}
          onClick={onToggleShuffle}
          aria-label={shuffle ? "シャッフルをオフにする" : "シャッフルをオンにする"}
          aria-pressed={shuffle}
        >
          <Shuffle size={20} />
        </button>
      )}

      <button className="playback-skip-btn" onClick={onSkipPrev} aria-label="前の曲">
        <SkipBack size={28} />
      </button>

      <button className="playback-main-btn" onClick={onPlayPause} aria-label={isPlaying ? "一時停止" : "再生"}>
        {isPlaying ? <Pause size={28} fill="white" /> : <Play size={28} fill="white" />}
      </button>

      <button className="playback-skip-btn" onClick={onSkipNext} aria-label="次の曲">
        <SkipForward size={28} />
      </button>

      {onCycleRepeat && (
        <div className="playback-mode-btn-wrapper">
          <button
            className={`playback-mode-btn${repeatMode !== "off" ? " playback-mode-btn--active" : ""}`}
            onClick={onCycleRepeat}
            aria-label={
              repeatMode === "off" ? "リピートをオンにする" :
              repeatMode === "all" ? "1曲リピートにする" : "リピートをオフにする"
            }
            aria-pressed={repeatMode !== "off"}
          >
            {repeatMode === "one" ? <Repeat1 size={20} /> : <Repeat size={20} />}
          </button>
          {repeatMode !== "off" && <span className="playback-mode-dot" aria-hidden="true" />}
        </div>
      )}
    </div>
  );
}
