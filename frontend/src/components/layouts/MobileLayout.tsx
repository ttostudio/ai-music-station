import type { Channel, Track } from "../../api/types";
import { TabBar, type Tab } from "../TabBar";
import { MiniPlayer } from "../MiniPlayer";
import { NowPlayingScreen } from "../NowPlayingScreen";
import { KaraokeScreen } from "../KaraokeScreen";
import { ChannelManager } from "../ChannelManager";
import { TrackHistory } from "../TrackHistory";
import { RequestForm } from "../RequestForm";
import { PlaylistList } from "../PlaylistList";
import { PlaylistDetail } from "../PlaylistDetail";
import { RequestQueueTab } from "../RequestQueueTab";
import { SearchBar } from "../SearchBar";
import { getChannelGradient, getChannelThemeKey } from "../../utils/lrc-parser";
import { getTracks } from "../../api/client";
import { Settings, Music, Heart } from "lucide-react";
import type { PlaylistPlayerResult } from "../../hooks/usePlaylistPlayer";

type Screen = "home" | "nowplaying" | "karaoke" | "manager" | "playlist-detail";

interface Props {
  channels: Channel[];
  activeSlug: string | null;
  activeChannel: Channel | undefined;
  track: Track | null;
  isPlaying: boolean;
  elapsedMs: number;
  durationMs: number;
  audioRef: React.RefObject<HTMLAudioElement | null>;
  activeTab: Tab;
  currentScreen: Screen;
  selectedPlaylistId: string | null;
  onTabChange: (tab: Tab) => void;
  onScreenChange: (screen: Screen) => void;
  onOpenPlaylist: (id: string) => void;
  onSelectChannel: (slug: string) => void;
  onTogglePlay: () => void;
  onSkipPrev: () => void;
  onSkipNext: () => void;
  onLike: () => void;
  liked?: boolean;
  playlistPlayer: PlaylistPlayerResult;
}

function getChannelIcon(slug: string): string {
  if (slug.includes("anime")) return "\uD83C\uDFA4";
  if (slug.includes("egushi") || slug.includes("えぐ")) return "\uD83C\uDFB5";
  if (slug.includes("game")) return "\uD83C\uDFAE";
  if (slug.includes("jazz")) return "\uD83C\uDFB7";
  if (slug.includes("podcast")) return "\uD83C\uDFA7";
  return "\uD83C\uDFB5";
}

async function fetchAllTracks(channels: Channel[]): Promise<Track[]> {
  const results = await Promise.all(
    channels.map((ch) => getTracks(ch.slug, 50).then((r) => r.tracks)),
  );
  return results.flat();
}

export function MobileLayout({
  channels,
  activeSlug,
  activeChannel,
  track,
  isPlaying,
  elapsedMs,
  durationMs,
  audioRef,
  activeTab,
  currentScreen,
  selectedPlaylistId,
  onTabChange,
  onScreenChange,
  onOpenPlaylist,
  onSelectChannel,
  onTogglePlay,
  onSkipPrev,
  onSkipNext,
  onLike,
  liked,
  playlistPlayer,
}: Props) {
  const channelName = activeChannel?.name ?? "";
  const visibleChannels = channels.filter((c) => c.is_active);
  const isTrackMode = playlistPlayer.playMode === "track";

  const handleToggleTrackPlay = () => {
    const audio = document.querySelector<HTMLAudioElement>("audio#track-audio");
    if (!audio) return;
    if (playlistPlayer.isTrackPlaying) {
      audio.pause();
    } else {
      audio.play().catch(() => {});
    }
  };

  // Sub-screens overlay on top
  if (currentScreen === "nowplaying") {
    return (
      <div className="mobile-layout">
        <NowPlayingScreen
          track={track}
          channelName={channelName}
          channelSlug={activeSlug}
          isPlaying={isPlaying}
          elapsedMs={elapsedMs}
          durationMs={durationMs}
          audioRef={audioRef}
          onBack={() => onScreenChange("home")}
          onPlayPause={onTogglePlay}
          onSkipPrev={onSkipPrev}
          onSkipNext={onSkipNext}
          onLike={onLike}
          onLyrics={() => onScreenChange("karaoke")}
          liked={liked}
        />
      </div>
    );
  }

  if (currentScreen === "karaoke") {
    return (
      <div className="mobile-layout">
        <KaraokeScreen
          track={track}
          isPlaying={isPlaying}
          elapsedMs={elapsedMs}
          durationMs={durationMs}
          onClose={() => onScreenChange("nowplaying")}
          onPlayPause={onTogglePlay}
        />
      </div>
    );
  }

  if (currentScreen === "manager") {
    return (
      <div className="mobile-layout">
        <ChannelManager onClose={() => onScreenChange("home")} />
      </div>
    );
  }

  if (currentScreen === "playlist-detail" && selectedPlaylistId) {
    return (
      <div className="mobile-layout">
        <PlaylistDetail
          playlistId={selectedPlaylistId}
          onBack={() => onScreenChange("home")}
          onDeleted={() => {
            onScreenChange("home");
            onTabChange("playlist");
          }}
          fetchAllTracks={() => fetchAllTracks(channels)}
          onPlayPlaylist={playlistPlayer.playPlaylist}
          onPlayTrack={playlistPlayer.playTrack}
          currentTrackId={isTrackMode ? playlistPlayer.currentTrack?.id : undefined}
        />
      </div>
    );
  }

  // Main tab view
  return (
    <div className="mobile-layout">
      <div className="mobile-content">
        {activeTab === "radio" && (
          <div className="mobile-radio-tab">
            {/* Header */}
            <header className="mobile-header">
              <div className="mobile-header-row">
                <div>
                  <h1 className="mobile-title">AI Music Station</h1>
                  <p className="mobile-subtitle">AIが生成した音楽をライブ配信</p>
                </div>
                <SearchBar
                  mobile
                  onPlayTrack={(t) => playlistPlayer.playTrack(t)}
                />
              </div>
              <button className="mobile-manage-btn" onClick={() => onScreenChange("manager")}>
                <Settings size={14} />
                <span>チャンネル管理</span>
              </button>
            </header>

            {/* Channel grid */}
            <div className="mobile-channel-grid" role="radiogroup" aria-label="チャンネル選択">
              {visibleChannels.map((ch) => {
                const isActive = ch.slug === activeSlug;
                const themeKey = getChannelThemeKey(ch.slug);
                return (
                  <button
                    key={ch.slug}
                    className={`mobile-channel-card ${isActive ? "mobile-channel-card-active" : ""}`}
                    onClick={() => onSelectChannel(ch.slug)}
                    role="radio"
                    aria-checked={isActive}
                    aria-label={`${ch.name}チャンネルを選択`}
                    data-theme={themeKey}
                  >
                    <span className="mobile-channel-icon" style={{ background: getChannelGradient(ch.slug) }}>
                      {getChannelIcon(ch.slug)}
                    </span>
                    <span className="mobile-channel-name">{ch.name}</span>
                    <span className="mobile-channel-count">{ch.total_tracks}曲</span>
                  </button>
                );
              })}
            </div>

            {/* Request form */}
            <RequestForm channels={channels} defaultSlug={activeSlug ?? undefined} />
          </div>
        )}

        {activeTab === "tracks" && (
          <div className="mobile-tracks-tab">
            <div className="mobile-tab-header">
              <Music size={20} />
              <span>再生履歴</span>
            </div>
            {activeSlug ? (
              <TrackHistory channelSlug={activeSlug} nowPlayingId={track?.id} />
            ) : (
              <div className="mobile-empty-state">チャンネルを選択してください</div>
            )}
          </div>
        )}

        {activeTab === "likes" && (
          <div className="mobile-likes-tab">
            <div className="mobile-tab-header">
              <Heart size={20} />
              <span>いいねした曲</span>
            </div>
            {activeSlug ? (
              <TrackHistory channelSlug={activeSlug} nowPlayingId={track?.id} />
            ) : (
              <div className="mobile-empty-state">チャンネルを選択してください</div>
            )}
          </div>
        )}

        {activeTab === "playlist" && (
          <PlaylistList onOpenDetail={onOpenPlaylist} />
        )}

        {activeTab === "queue" && (
          <RequestQueueTab />
        )}
      </div>

      {/* Mini player */}
      {(activeSlug || isTrackMode) && (
        <MiniPlayer
          track={track}
          channelName={channelName}
          isPlaying={isPlaying}
          onPlayPause={onTogglePlay}
          onOpenNowPlaying={() => onScreenChange("nowplaying")}
          playMode={playlistPlayer.playMode}
          currentTrack={playlistPlayer.currentTrack}
          isTrackPlaying={playlistPlayer.isTrackPlaying}
          trackElapsedMs={playlistPlayer.trackElapsedMs}
          trackDurationMs={playlistPlayer.trackDurationMs}
          onNextTrack={playlistPlayer.nextTrack}
          onPrevTrack={playlistPlayer.prevTrack}
          onToggleTrackPlay={handleToggleTrackPlay}
        />
      )}

      {/* Tab bar */}
      <TabBar activeTab={activeTab} onChange={onTabChange} />
    </div>
  );
}
