import { ChevronDown, MoreHorizontal } from "lucide-react";
import type { Track } from "../api/types";
import type { RepeatMode } from "../hooks/usePlaylistPlayer";
import { AudioVisualizer } from "./AudioVisualizer";
import { PlaybackControls } from "./PlaybackControls";
import { ActionButtons } from "./ActionButtons";
import { ProgressBar } from "./ProgressBar";

interface Props {
  track: Track | null;
  channelName: string;
  channelSlug: string | null;
  isPlaying: boolean;
  elapsedMs: number;
  durationMs: number;
  audioRef: React.RefObject<HTMLAudioElement | null>;
  onBack: () => void;
  onPlayPause: () => void;
  onSkipPrev: () => void;
  onSkipNext: () => void;
  onLike: () => void;
  onLyrics: () => void;
  liked?: boolean;
  shuffle?: boolean;
  repeatMode?: RepeatMode;
  onToggleShuffle?: () => void;
  onCycleRepeat?: () => void;
}

export function NowPlayingScreen({
  track,
  channelName,
  channelSlug,
  isPlaying,
  elapsedMs,
  durationMs,
  audioRef,
  onBack,
  onPlayPause,
  onSkipPrev,
  onSkipNext,
  onLike,
  onLyrics,
  liked,
  shuffle,
  repeatMode,
  onToggleShuffle,
  onCycleRepeat,
}: Props) {
  const title = track ? (track.title || track.caption) : "";
  const artist = `AI Music Station \u2022 ${channelName}`;

  return (
    <div className="now-playing-screen">
      {/* Nav bar */}
      <div className="np-navbar">
        <button className="np-nav-btn" onClick={onBack} aria-label="戻る">
          <ChevronDown size={28} />
        </button>
        <span className="np-nav-title">{channelName}</span>
        <button className="np-nav-btn" aria-label="メニュー">
          <MoreHorizontal size={24} />
        </button>
      </div>

      {/* Visualizer area */}
      <div className="np-visualizer-area">
        <AudioVisualizer audioRef={audioRef} isPlaying={isPlaying} channelSlug={channelSlug} />
      </div>

      {/* Track info */}
      <div className="np-track-info">
        <h2 className="np-title">{title}</h2>
        <p className="np-artist">{artist}</p>
      </div>

      {/* Progress bar */}
      <div className="np-progress">
        <ProgressBar currentMs={elapsedMs} totalMs={durationMs} />
      </div>

      {/* Playback controls */}
      <PlaybackControls
        isPlaying={isPlaying}
        onPlayPause={onPlayPause}
        onSkipPrev={onSkipPrev}
        onSkipNext={onSkipNext}
        shuffle={shuffle}
        repeatMode={repeatMode}
        onToggleShuffle={onToggleShuffle}
        onCycleRepeat={onCycleRepeat}
      />

      {/* Action buttons */}
      <ActionButtons liked={liked} trackId={track?.id} onLike={onLike} onLyrics={onLyrics} />
    </div>
  );
}
