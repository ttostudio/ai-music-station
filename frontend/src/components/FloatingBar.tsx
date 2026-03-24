import { Play, Pause, Heart, Captions, Radio } from "lucide-react";
import type { Track } from "../api/types";
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
}: Props) {
  const title = track ? (track.title || track.caption) : "";
  const pct = durationMs > 0 ? Math.min((elapsedMs / durationMs) * 100, 100) : 0;

  return (
    <div className="floating-bar" role="region" aria-label="プレイヤー">
      {/* Play button */}
      <button className="fb-play-btn" onClick={onPlayPause} aria-label={isPlaying ? "一時停止" : "再生"}>
        {isPlaying ? <Pause size={20} fill="black" color="black" /> : <Play size={20} fill="black" color="black" />}
      </button>

      {/* Track info */}
      <div className="fb-info">
        <div className="fb-title">{title}</div>
        <div className="fb-channel">{channelName}</div>
      </div>

      {/* Progress bar */}
      <div className="fb-progress">
        <div className="fb-progress-track">
          <div className="fb-progress-fill" style={{ width: `${pct}%` }} />
        </div>
      </div>

      {/* Time */}
      <span className="fb-time">{formatTime(elapsedMs)} / {formatTime(durationMs)}</span>

      {/* Like */}
      <button className="fb-icon-btn" onClick={onLike} aria-label={liked ? "いいね解除" : "いいね"}>
        <Heart size={18} fill={liked ? "#ec4899" : "none"} color={liked ? "#ec4899" : "rgba(255,255,255,0.25)"} />
      </button>

      {/* Lyrics toggle */}
      <button
        className={`fb-icon-btn ${lyricsActive ? "fb-icon-active" : ""}`}
        onClick={onLyricsToggle}
        aria-label="歌詞パネル"
      >
        <Captions size={18} color={lyricsActive ? "#FFFFFF" : "#8b5cf6"} />
      </button>

      {/* Share */}
      <ShareButton trackId={track?.id ?? null} size={18} color="rgba(255,255,255,0.25)" className="fb-share-btn" />

      {/* Channel menu */}
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
    </div>
  );
}
