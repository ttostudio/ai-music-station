import { Play, Pause, Heart, Captions, Radio, ListMusic, SkipBack, SkipForward, Shuffle, Repeat, Repeat1 } from "lucide-react";
import type { Track } from "../api/types";
import type { PlayMode, RepeatMode } from "../hooks/usePlaylistPlayer";
import { formatTime } from "../utils/lrc-parser";
import { ShareButton } from "./ShareButton";

interface Props {
  track: Track | null;
  channelName: string;
  isPlaying: boolean;
  elapsedMs: number;
  durationMs: number;
  lyricsActive: boolean;
  onPlayPause: () => void;
  onLike: () => void;
  onLyricsToggle: () => void;
  onChannelMenu: () => void;
  liked?: boolean;
  // Track mode props
  playMode?: PlayMode;
  currentTrack?: Track | null;
  isTrackPlaying?: boolean;
  trackElapsedMs?: number;
  trackDurationMs?: number;
  shuffle?: boolean;
  repeat?: RepeatMode;
  onToggleMode?: () => void;
  onNextTrack?: () => void;
  onPrevTrack?: () => void;
  onToggleTrackPlay?: () => void;
  onToggleShuffle?: () => void;
  onCycleRepeat?: () => void;
  onSeekTo?: (ratio: number) => void;
}

export function FloatingBar({
  track,
  channelName,
  isPlaying,
  elapsedMs,
  durationMs,
  lyricsActive,
  onPlayPause,
  onLike,
  onLyricsToggle,
  onChannelMenu,
  liked,
  playMode = "stream",
  currentTrack,
  isTrackPlaying = false,
  trackElapsedMs = 0,
  trackDurationMs = 0,
  shuffle = false,
  repeat = "off",
  onToggleMode,
  onNextTrack,
  onPrevTrack,
  onToggleTrackPlay,
  onToggleShuffle,
  onCycleRepeat,
  onSeekTo,
}: Props) {
  const isTrackMode = playMode === "track";

  // Display values based on mode
  const displayTrack = isTrackMode ? currentTrack : track;
  const displayPlaying = isTrackMode ? isTrackPlaying : isPlaying;
  const displayElapsed = isTrackMode ? trackElapsedMs : elapsedMs;
  const displayDuration = isTrackMode ? trackDurationMs : durationMs;
  const title = displayTrack ? (displayTrack.title || displayTrack.caption) : "";
  const pct = displayDuration > 0 ? Math.min((displayElapsed / displayDuration) * 100, 100) : 0;

  const handlePlayPause = () => {
    if (isTrackMode && onToggleTrackPlay) {
      onToggleTrackPlay();
    } else {
      onPlayPause();
    }
  };

  const handleSeek = (e: React.MouseEvent<HTMLDivElement>) => {
    if (!isTrackMode || !onSeekTo || displayDuration === 0) return;
    const rect = e.currentTarget.getBoundingClientRect();
    const ratio = Math.max(0, Math.min(1, (e.clientX - rect.left) / rect.width));
    onSeekTo(ratio);
  };

  const RepeatIcon = repeat === "one" ? Repeat1 : Repeat;

  return (
    <div className="floating-bar" role="region" aria-label="プレイヤー">
      {/* Mode toggle */}
      {onToggleMode && (
        <button
          className={`fb-mode-btn ${isTrackMode ? "fb-mode-btn-track" : ""}`}
          onClick={onToggleMode}
          aria-label={isTrackMode ? "ストリームモードへ切替" : "トラックモードへ切替"}
          title={isTrackMode ? "RADIOモードへ" : "TRACKモードへ"}
        >
          {isTrackMode ? <ListMusic size={16} /> : <Radio size={16} />}
        </button>
      )}

      {/* Prev (track mode only) */}
      {isTrackMode && (
        <button
          className="fb-nav-btn"
          onClick={onPrevTrack}
          aria-label="前のトラック"
        >
          <SkipBack size={16} />
        </button>
      )}

      {/* Play button */}
      <button className="fb-play-btn" onClick={handlePlayPause} aria-label={displayPlaying ? "一時停止" : "再生"}>
        {displayPlaying ? <Pause size={20} fill="black" color="black" /> : <Play size={20} fill="black" color="black" />}
      </button>

      {/* Next (track mode only) */}
      {isTrackMode && (
        <button
          className="fb-nav-btn"
          onClick={onNextTrack}
          aria-label="次のトラック"
        >
          <SkipForward size={16} />
        </button>
      )}

      {/* Track info */}
      <div className="fb-info">
        <div className="fb-title">{title}</div>
        <div className="fb-channel">{isTrackMode ? "トラックモード" : channelName}</div>
      </div>

      {/* Progress bar */}
      <div
        className={`fb-progress ${isTrackMode ? "fb-progress-seekable" : ""}`}
        onClick={handleSeek}
        role={isTrackMode ? "slider" : undefined}
        aria-label={isTrackMode ? "再生位置" : undefined}
        aria-valuenow={isTrackMode ? Math.round(pct) : undefined}
        aria-valuemin={isTrackMode ? 0 : undefined}
        aria-valuemax={isTrackMode ? 100 : undefined}
      >
        <div className="fb-progress-track">
          <div className="fb-progress-fill" style={{ width: `${pct}%` }} />
        </div>
      </div>

      {/* Time */}
      <span className="fb-time">{formatTime(displayElapsed)} / {formatTime(displayDuration)}</span>

      {/* Shuffle (track mode only) */}
      {isTrackMode && (
        <button
          className={`fb-icon-btn ${shuffle ? "fb-icon-active" : ""}`}
          onClick={onToggleShuffle}
          aria-label={shuffle ? "シャッフルOFF" : "シャッフルON"}
          aria-pressed={shuffle}
        >
          <Shuffle size={16} color={shuffle ? "#FFFFFF" : "rgba(255,255,255,0.35)"} />
        </button>
      )}

      {/* Repeat (track mode only) */}
      {isTrackMode && (
        <button
          className={`fb-icon-btn ${repeat !== "off" ? "fb-icon-active" : ""}`}
          onClick={onCycleRepeat}
          aria-label={repeat === "off" ? "リピートOFF" : repeat === "all" ? "全曲リピート" : "1曲リピート"}
          aria-pressed={repeat !== "off"}
        >
          <RepeatIcon size={16} color={repeat !== "off" ? "#FFFFFF" : "rgba(255,255,255,0.35)"} />
        </button>
      )}

      {/* Like (stream mode) */}
      {!isTrackMode && (
        <button className="fb-icon-btn" onClick={onLike} aria-label={liked ? "いいね解除" : "いいね"}>
          <Heart size={18} fill={liked ? "#ec4899" : "none"} color={liked ? "#ec4899" : "rgba(255,255,255,0.25)"} />
        </button>
      )}

      {/* Lyrics toggle (stream mode) */}
      {!isTrackMode && (
        <button
          className={`fb-icon-btn ${lyricsActive ? "fb-icon-active" : ""}`}
          onClick={onLyricsToggle}
          aria-label="歌詞パネル"
        >
          <Captions size={18} color={lyricsActive ? "#FFFFFF" : "#8b5cf6"} />
        </button>
      )}

      {/* Share */}
      <ShareButton trackId={displayTrack?.id ?? null} size={18} color="rgba(255,255,255,0.25)" className="fb-share-btn" />

      {/* Channel menu (stream mode only) */}
      {!isTrackMode && (
        <button
          className="fb-channel-btn"
          onClick={onChannelMenu}
          aria-haspopup="menu"
          aria-label="チャンネルメニュー"
        >
          <Radio size={14} />
          <span>{channelName || "チャンネル"}</span>
          <span className="fb-channel-arrow">&#9650;</span>
        </button>
      )}
    </div>
  );
}
