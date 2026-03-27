import { useState } from "react";
import type { Channel, Track } from "../../api/types";
import { TheaterView } from "../TheaterView";
import { FloatingBar } from "../FloatingBar";
import { ChannelMenu } from "../ChannelMenu";
import { LyricsPanel } from "../LyricsPanel";
import { RequestForm } from "../RequestForm";
import { SearchBar } from "../SearchBar";
import type { PlaylistPlayerResult } from "../../hooks/usePlaylistPlayer";

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
  playlistPlayer: PlaylistPlayerResult;
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
  playlistPlayer,
}: Props) {
  const channelName = activeChannel?.name ?? "";
  const lyrics = track?.lyrics ?? "";
  const [showRequestPanel, setShowRequestPanel] = useState(false);
  const isTrackMode = playlistPlayer.playMode === "track";

  const handleToggleMode = () => {
    if (isTrackMode) {
      playlistPlayer.switchToStream();
    } else {
      playlistPlayer.switchToTrack();
    }
  };

  const handleToggleTrackPlay = () => {
    const audio = document.querySelector<HTMLAudioElement>("audio#track-audio");
    if (!audio) return;
    if (playlistPlayer.isTrackPlaying) {
      audio.pause();
    } else {
      audio.play().catch(() => {});
    }
  };

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

      {/* Search bar */}
      <div className="desktop-search-bar">
        <SearchBar onPlayTrack={(t) => playlistPlayer.playTrack(t)} />
      </div>

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
        playMode={playlistPlayer.playMode}
        currentTrack={playlistPlayer.currentTrack}
        isTrackPlaying={playlistPlayer.isTrackPlaying}
        trackElapsedMs={playlistPlayer.trackElapsedMs}
        trackDurationMs={playlistPlayer.trackDurationMs}
        shuffle={playlistPlayer.shuffle}
        repeat={playlistPlayer.repeat}
        onToggleMode={handleToggleMode}
        onNextTrack={playlistPlayer.nextTrack}
        onPrevTrack={playlistPlayer.prevTrack}
        onToggleTrackPlay={handleToggleTrackPlay}
        onToggleShuffle={playlistPlayer.toggleShuffle}
        onCycleRepeat={playlistPlayer.cycleRepeat}
        onSeekTo={playlistPlayer.seekTo}
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

      {/* Request panel toggle button */}
      <button
        className="desktop-request-toggle"
        onClick={() => setShowRequestPanel((v) => !v)}
        aria-label="リクエストパネルを開く"
      >
        ♪ リクエスト
      </button>

      {/* Request panel */}
      {showRequestPanel && (
        <div className="desktop-request-panel">
          <RequestForm channels={channels} defaultSlug={activeSlug ?? undefined} />
        </div>
      )}
    </div>
  );
}
