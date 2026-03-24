import { ChevronDown, X, Play, Pause } from "lucide-react";
import type { Track } from "../api/types";
import { KaraokeOverlay } from "./KaraokeOverlay";
import { LyricsScrollPanel } from "./LyricsScrollPanel";
import { formatTime } from "../utils/lrc-parser";

interface Props {
  track: Track | null;
  isPlaying: boolean;
  elapsedMs: number;
  durationMs: number;
  onClose: () => void;
  onPlayPause: () => void;
}

export function KaraokeScreen({ track, isPlaying, elapsedMs, durationMs, onClose, onPlayPause }: Props) {
  const title = track ? (track.title || track.caption) : "";
  const lyrics = track?.lyrics ?? "";

  return (
    <div className="karaoke-screen">
      {/* Nav */}
      <div className="karaoke-nav">
        <button className="np-nav-btn" onClick={onClose} aria-label="戻る">
          <ChevronDown size={24} />
        </button>
        <span className="karaoke-nav-title">{title}</span>
        <button className="np-nav-btn" onClick={onClose} aria-label="閉じる">
          <X size={24} />
        </button>
      </div>

      {/* Karaoke hero area */}
      {lyrics && (
        <div className="karaoke-hero-area">
          <KaraokeOverlay lyrics={lyrics} elapsedMs={elapsedMs} durationMs={durationMs} variant="mobile" />
        </div>
      )}

      {/* Divider */}
      <div className="karaoke-divider" />

      {/* Full lyrics scroll */}
      {lyrics && (
        <div className="karaoke-lyrics-scroll">
          <LyricsScrollPanel lyrics={lyrics} elapsedMs={elapsedMs} durationMs={durationMs} variant="mobile" />
        </div>
      )}

      {/* Mini player at bottom */}
      <div className="karaoke-mini-player">
        <button
          className="karaoke-mini-play-btn"
          onClick={onPlayPause}
          aria-label={isPlaying ? "一時停止" : "再生"}
        >
          {isPlaying ? <Pause size={16} fill="white" /> : <Play size={16} fill="white" />}
        </button>
        <span className="karaoke-mini-title">{title}</span>
        <span className="karaoke-mini-time">
          {formatTime(elapsedMs)} / {formatTime(durationMs)}
        </span>
      </div>
    </div>
  );
}
