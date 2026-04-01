import { Play, Pause, Volume2, SkipBack, SkipForward, Shuffle, Repeat, Repeat1 } from "lucide-react";
import type { Track } from "../api/types";
import type { PlayMode, RepeatMode } from "../hooks/usePlaylistPlayer";

interface Props {
  track: Track | null;
  channelName: string;
  isPlaying: boolean;
  onPlayPause: () => void;
  onOpenNowPlaying: () => void;
  // Track mode props
  playMode?: PlayMode;
  currentTrack?: Track | null;
  isTrackPlaying?: boolean;
  trackElapsedMs?: number;
  trackDurationMs?: number;
  onNextTrack?: () => void;
  onPrevTrack?: () => void;
  onToggleTrackPlay?: () => void;
  shuffle?: boolean;
  repeatMode?: RepeatMode;
  onToggleShuffle?: () => void;
  onCycleRepeat?: () => void;
}

export function MiniPlayer({
  track,
  channelName,
  isPlaying,
  onPlayPause,
  onOpenNowPlaying,
  playMode = "stream",
  currentTrack,
  isTrackPlaying = false,
  trackElapsedMs = 0,
  trackDurationMs = 0,
  onNextTrack,
  onPrevTrack,
  onToggleTrackPlay,
  shuffle,
  repeatMode,
  onToggleShuffle,
  onCycleRepeat,
}: Props) {
  const isTrackMode = playMode === "track";
  const displayTrack = isTrackMode ? currentTrack : track;
  const displayPlaying = isTrackMode ? isTrackPlaying : isPlaying;
  const title = displayTrack ? (displayTrack.title || displayTrack.caption) : "再生を開始してください";
  const progress = isTrackMode && trackDurationMs > 0 ? Math.min(trackElapsedMs / trackDurationMs, 1) : 0;

  const handlePlayPause = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (isTrackMode && onToggleTrackPlay) {
      onToggleTrackPlay();
    } else {
      onPlayPause();
    }
  };

  return (
    <div className="miniplayer" onClick={onOpenNowPlaying} role="button" tabIndex={0} aria-label="Now Playingを開く">
      <button
        className="miniplayer-play-btn"
        onClick={handlePlayPause}
        aria-label={displayPlaying ? "一時停止" : "再生"}
      >
        {displayPlaying ? <Pause size={22} fill="white" /> : <Play size={22} fill="white" />}
      </button>

      <div className="miniplayer-info">
        <div className="miniplayer-title">{title}</div>
        <div className="miniplayer-channel">
          {isTrackMode ? "トラックモード" : channelName}
        </div>
        {isTrackMode && trackDurationMs > 0 && (
          <div className="miniplayer-progress-bar">
            <div
              className="miniplayer-progress-fill"
              style={{ width: `${progress * 100}%` }}
            />
          </div>
        )}
      </div>

      {isTrackMode ? (
        <div className="miniplayer-track-controls" onClick={(e) => e.stopPropagation()}>
          {onToggleShuffle && (
            <button
              className={`miniplayer-mode-btn${shuffle ? " miniplayer-mode-btn--active" : ""}`}
              onClick={(e) => { e.stopPropagation(); onToggleShuffle(); }}
              aria-label={shuffle ? "シャッフルをオフにする" : "シャッフルをオンにする"}
              aria-pressed={shuffle}
            >
              <Shuffle size={16} />
            </button>
          )}
          <button
            className="miniplayer-nav-btn"
            onClick={(e) => { e.stopPropagation(); onPrevTrack?.(); }}
            aria-label="前のトラック"
          >
            <SkipBack size={18} />
          </button>
          <button
            className="miniplayer-nav-btn"
            onClick={(e) => { e.stopPropagation(); onNextTrack?.(); }}
            aria-label="次のトラック"
          >
            <SkipForward size={18} />
          </button>
          {onCycleRepeat && (
            <button
              className={`miniplayer-mode-btn${repeatMode !== "off" ? " miniplayer-mode-btn--active" : ""}`}
              onClick={(e) => { e.stopPropagation(); onCycleRepeat(); }}
              aria-label={
                repeatMode === "off" ? "リピートをオンにする" :
                repeatMode === "all" ? "1曲リピートにする" : "リピートをオフにする"
              }
              aria-pressed={repeatMode !== "off"}
            >
              {repeatMode === "one" ? <Repeat1 size={16} /> : <Repeat size={16} />}
            </button>
          )}
        </div>
      ) : (
        <Volume2 size={20} className="miniplayer-volume" aria-hidden="true" />
      )}
    </div>
  );
}
