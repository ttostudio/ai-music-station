import type { Channel, Track } from "../../api/types";
import { TheaterView } from "../TheaterView";
import { FloatingBar } from "../FloatingBar";
import { ChannelMenu } from "../ChannelMenu";
import { LyricsPanel } from "../LyricsPanel";

interface Props {
  channels: Channel[];
  activeSlug: string | null;
  activeChannel: Channel | undefined;
  track: Track | null;
  isPlaying: boolean;
  elapsedMs: number;
  durationMs: number;
  audioRef: React.RefObject<HTMLAudioElement | null>;
  showLyricsPanel: boolean;
  showChannelMenu: boolean;
  onTogglePlay: () => void;
  onLike: () => void;
  onSelectChannel: (slug: string) => void;
  onLyricsPanelToggle: () => void;
  onChannelMenuToggle: () => void;
  onShowManager: () => void;
  liked?: boolean;
}

export function DesktopLayout({
  channels,
  activeSlug,
  activeChannel,
  track,
  isPlaying,
  elapsedMs,
  durationMs,
  audioRef,
  showLyricsPanel,
  showChannelMenu,
  onTogglePlay,
  onLike,
  onSelectChannel,
  onLyricsPanelToggle,
  onChannelMenuToggle,
  onShowManager,
  liked,
}: Props) {
  const channelName = activeChannel?.name ?? "";
  const lyrics = track?.lyrics ?? "";

  return (
    <div className="desktop-layout">
      <TheaterView
        audioRef={audioRef}
        isPlaying={isPlaying}
        channelSlug={activeSlug}
        lyrics={lyrics || undefined}
        elapsedMs={elapsedMs}
        durationMs={durationMs}
      />

      {/* Lyrics panel overlay */}
      {showLyricsPanel && (
        <LyricsPanel
          track={track}
          channelName={channelName}
          elapsedMs={elapsedMs}
          durationMs={durationMs}
          onClose={onLyricsPanelToggle}
        />
      )}

      {/* Floating bar */}
      <FloatingBar
        track={track}
        channelName={channelName}
        isPlaying={isPlaying}
        elapsedMs={elapsedMs}
        durationMs={durationMs}
        lyricsActive={showLyricsPanel}
        onPlayPause={onTogglePlay}
        onLike={onLike}
        onLyricsToggle={onLyricsPanelToggle}
        onChannelMenu={onChannelMenuToggle}
        liked={liked}
      />

      {/* Channel menu popup */}
      {showChannelMenu && (
        <div className="desktop-channel-menu-anchor">
          <ChannelMenu
            channels={channels}
            activeSlug={activeSlug}
            onSelect={onSelectChannel}
            onManage={onShowManager}
            onClose={onChannelMenuToggle}
          />
        </div>
      )}
    </div>
  );
}
