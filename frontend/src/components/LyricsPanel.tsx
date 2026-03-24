import { X } from "lucide-react";
import type { Track } from "../api/types";
import { LyricsScrollPanel } from "./LyricsScrollPanel";

interface Props {
  track: Track | null;
  channelName: string;
  elapsedMs: number;
  durationMs: number;
  onClose: () => void;
}

export function LyricsPanel({ track, channelName, elapsedMs, durationMs, onClose }: Props) {
  const title = track ? (track.title || track.caption) : "";
  const lyrics = track?.lyrics ?? "";

  return (
    <div className="lyrics-panel-overlay" role="complementary" aria-label="歌詞">
      <div className="lyrics-panel-header">
        <div>
          <div className="lyrics-panel-label">LYRICS</div>
          <div className="lyrics-panel-track-name">{title}</div>
          <div className="lyrics-panel-channel">{channelName}</div>
        </div>
        <button className="lyrics-panel-close" onClick={onClose} aria-label="歌詞パネルを閉じる">
          <X size={20} />
        </button>
      </div>
      <div className="lyrics-panel-divider" />
      <div className="lyrics-panel-scroll">
        {lyrics ? (
          <LyricsScrollPanel lyrics={lyrics} elapsedMs={elapsedMs} durationMs={durationMs} variant="panel" />
        ) : (
          <div className="lyrics-panel-empty">歌詞がありません</div>
        )}
      </div>
    </div>
  );
}
