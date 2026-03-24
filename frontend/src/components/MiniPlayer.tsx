import { Play, Pause, Volume2 } from "lucide-react";
import type { Track } from "../api/types";

interface Props {
  track: Track | null;
  channelName: string;
  isPlaying: boolean;
  onPlayPause: () => void;
  onOpenNowPlaying: () => void;
}

export function MiniPlayer({ track, channelName, isPlaying, onPlayPause, onOpenNowPlaying }: Props) {
  const title = track ? (track.title || track.caption) : "再生を開始してください";

  return (
    <div className="miniplayer" onClick={onOpenNowPlaying} role="button" tabIndex={0} aria-label="Now Playingを開く">
      <button
        className="miniplayer-play-btn"
        onClick={(e) => { e.stopPropagation(); onPlayPause(); }}
        aria-label={isPlaying ? "一時停止" : "再生"}
      >
        {isPlaying ? <Pause size={22} fill="white" /> : <Play size={22} fill="white" />}
      </button>

      <div className="miniplayer-info">
        <div className="miniplayer-title">{title}</div>
        <div className="miniplayer-channel">{channelName}</div>
      </div>

      <Volume2 size={20} className="miniplayer-volume" aria-hidden="true" />
    </div>
  );
}
