import { useState } from "react";
import type { Channel, Track } from "../../api/types";
import { TheaterView } from "../TheaterView";
import { FloatingBar } from "../FloatingBar";
import { ChannelMenu } from "../ChannelMenu";
import { LyricsScrollPanel } from "../LyricsScrollPanel";
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
  showChannelMenu: boolean;
  onTogglePlay: () => void;
  onLike: () => void;
  onSelectChannel: (slug: string) => void;
  onChannelMenuToggle: () => void;
  onShowManager: () => void;
  liked?: boolean;
  playlistPlayer: PlaylistPlayerResult;
}

export function TabletLayout({
  channels,
  activeSlug,
  activeChannel,
  track,
  isPlaying,
  elapsedMs,
  durationMs,
  audioRef,
  showChannelMenu,
  onTogglePlay,
  onLike,
  onSelectChannel,
  onChannelMenuToggle,
  onShowManager,
  liked,
  playlistPlayer,
}: Props) {
  const [showLyrics, setShowLyrics] = useState(true);
  const channelName = activeChannel?.name ?? "";
  const lyrics = track?.lyrics ?? "";
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
    <div className="tablet-layout">
      {/* Upper theater half */}
      <div className="tablet-upper">
        <TheaterView
          audioRef={audioRef}
          isPlaying={isPlaying}
          channelSlug={activeSlug}
          lyrics={lyrics || undefined}
          elapsedMs={elapsedMs}
          durationMs={durationMs}
        />

        <div className="tablet-floating-bar-wrapper">
          {/* Search bar */}
          <div className="tablet-search-bar">
            <SearchBar onPlayTrack={(t) => playlistPlayer.playTrack(t)} />
          </div>

          <FloatingBar
            track={track}
            channelName={channelName}
            isPlaying={isPlaying}
            elapsedMs={elapsedMs}
            durationMs={durationMs}
            lyricsActive={showLyrics}
            onPlayPause={onTogglePlay}
            onLike={onLike}
            onLyricsToggle={() => setShowLyrics((v) => !v)}
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
          {showChannelMenu && (
            <ChannelMenu
              channels={channels}
              activeSlug={activeSlug}
              onSelect={onSelectChannel}
              onManage={onShowManager}
              onClose={onChannelMenuToggle}
            />
          )}
        </div>
      </div>

      {/* Lower: lyrics + request form */}
      <div className="tablet-lower">
        {showLyrics && (
          lyrics ? (
            <LyricsScrollPanel lyrics={lyrics} elapsedMs={elapsedMs} durationMs={durationMs} variant="tablet" />
          ) : (
            <div className="tablet-no-lyrics">♪ インストゥルメンタル</div>
          )
        )}
        <div className="px-4 pb-4">
          <RequestForm channels={channels} defaultSlug={activeSlug ?? undefined} />
        </div>
      </div>
    </div>
  );
}
