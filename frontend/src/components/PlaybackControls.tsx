import { Play, Pause, SkipBack, SkipForward } from "lucide-react";

interface Props {
  isPlaying: boolean;
  onPlayPause: () => void;
  onSkipPrev: () => void;
  onSkipNext: () => void;
}

export function PlaybackControls({ isPlaying, onPlayPause, onSkipPrev, onSkipNext }: Props) {
  return (
    <div className="playback-controls">
      <button className="playback-skip-btn" onClick={onSkipPrev} aria-label="前の曲">
        <SkipBack size={28} />
      </button>

      <button className="playback-main-btn" onClick={onPlayPause} aria-label={isPlaying ? "一時停止" : "再生"}>
        {isPlaying ? <Pause size={28} fill="white" /> : <Play size={28} fill="white" />}
      </button>

      <button className="playback-skip-btn" onClick={onSkipNext} aria-label="次の曲">
        <SkipForward size={28} />
      </button>
    </div>
  );
}
