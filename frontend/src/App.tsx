import { useState, useRef, useCallback } from "react";
import { Player } from "./components/Player";
import { useChannels } from "./hooks/useChannels";
import { useNowPlaying } from "./hooks/useNowPlaying";
import { useElapsedTime } from "./hooks/useElapsedTime";
import { useKeyboardShortcuts } from "./hooks/useKeyboardShortcuts";
import { useBreakpoint } from "./hooks/useBreakpoint";
import { resumeAudioContext } from "./components/AudioVisualizer";
import { MobileLayout } from "./components/layouts/MobileLayout";
import { TabletLayout } from "./components/layouts/TabletLayout";
import { DesktopLayout } from "./components/layouts/DesktopLayout";

export default function App() {
  const { channels, loading, error } = useChannels();
  const [activeSlug, setActiveSlug] = useState<string | null>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [volume, setVolume] = useState(0.8);
  const prevVolumeRef = useRef(0.8);
  const nowPlaying = useNowPlaying(activeSlug);

  // New state for redesign
  const [activeTab, setActiveTab] = useState<"radio" | "tracks" | "likes">("radio");
  const [currentScreen, setCurrentScreen] = useState<"home" | "nowplaying" | "karaoke" | "manager">("home");
  const [showLyricsPanel, setShowLyricsPanel] = useState(false);
  const [showChannelMenu, setShowChannelMenu] = useState(false);
  const [liked, setLiked] = useState(false);

  const breakpoint = useBreakpoint();

  const activeChannel = channels.find((c) => c.slug === activeSlug);
  const streamUrl = activeChannel ? activeChannel.stream_url : null;

  // Shared audioRef — passed to Player and layouts
  const audioRef = useRef<HTMLAudioElement>(null);
  const elapsedMs = useElapsedTime(audioRef, isPlaying);

  const togglePlay = useCallback(async () => {
    if (!audioRef.current || !streamUrl) return;
    try {
      if (isPlaying) {
        audioRef.current.pause();
        setIsPlaying(false);
      } else {
        resumeAudioContext(audioRef.current);
        await audioRef.current.play();
        setIsPlaying(true);
      }
    } catch {
      setIsPlaying(false);
    }
  }, [isPlaying, streamUrl]);

  const handleVolumeUp = useCallback(() => {
    setVolume((v) => Math.min(1, +(v + 0.05).toFixed(2)));
  }, []);

  const handleVolumeDown = useCallback(() => {
    setVolume((v) => Math.max(0, +(v - 0.05).toFixed(2)));
  }, []);

  const handleMute = useCallback(() => {
    setVolume((v) => {
      if (v > 0) {
        prevVolumeRef.current = v;
        return 0;
      }
      return prevVolumeRef.current || 0.8;
    });
  }, []);

  const handleSelectChannel = useCallback(
    (index: number) => {
      if (index < channels.length) {
        setActiveSlug(channels[index].slug);
      }
    },
    [channels],
  );

  const handleSelectChannelBySlug = useCallback((slug: string) => {
    setActiveSlug(slug);
  }, []);

  const handleSkipNext = useCallback(() => {
    if (!activeSlug || channels.length === 0) return;
    const activeChannels = channels.filter((c) => c.is_active);
    const idx = activeChannels.findIndex((c) => c.slug === activeSlug);
    if (idx >= 0 && idx < activeChannels.length - 1) {
      setActiveSlug(activeChannels[idx + 1].slug);
    }
  }, [activeSlug, channels]);

  const handleSkipPrev = useCallback(() => {
    if (!activeSlug || channels.length === 0) return;
    const activeChannels = channels.filter((c) => c.is_active);
    const idx = activeChannels.findIndex((c) => c.slug === activeSlug);
    if (idx > 0) {
      setActiveSlug(activeChannels[idx - 1].slug);
    }
  }, [activeSlug, channels]);

  const handleLike = useCallback(() => {
    setLiked((v) => !v);
  }, []);

  useKeyboardShortcuts({
    onTogglePlay: togglePlay,
    onVolumeUp: handleVolumeUp,
    onVolumeDown: handleVolumeDown,
    onMute: handleMute,
    onSelectChannel: handleSelectChannel,
  });

  if (loading) {
    return (
      <div className="loading-screen">
        <div className="loading-text">チャンネルを読み込み中...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="loading-screen">
        <div className="error-text">{error}</div>
      </div>
    );
  }

  const durationMs = nowPlaying?.duration_ms ?? 0;

  return (
    <div className="app-root">
      {/* Hidden audio element — Player.tsx manages audio tag with crossOrigin and preload */}
      <div style={{ display: "none" }}>
        <Player
          streamUrl={streamUrl}
          channelName={activeChannel?.name ?? ""}
          nowPlaying={nowPlaying}
          elapsedMs={elapsedMs}
          durationMs={durationMs}
          audioRef={audioRef}
          volume={volume}
          onVolumeChange={setVolume}
          isPlaying={isPlaying}
          onTogglePlay={togglePlay}
        />
      </div>

      {/* Mobile layout */}
      {breakpoint === "mobile" && (
        <MobileLayout
          channels={channels}
          activeSlug={activeSlug}
          activeChannel={activeChannel}
          track={nowPlaying}
          isPlaying={isPlaying}
          elapsedMs={elapsedMs}
          durationMs={durationMs}
          audioRef={audioRef}
          activeTab={activeTab}
          currentScreen={currentScreen}
          onTabChange={setActiveTab}
          onScreenChange={setCurrentScreen}
          onSelectChannel={handleSelectChannelBySlug}
          onTogglePlay={togglePlay}
          onSkipPrev={handleSkipPrev}
          onSkipNext={handleSkipNext}
          onLike={handleLike}
          liked={liked}
        />
      )}

      {/* Tablet layout */}
      {breakpoint === "tablet" && (
        <TabletLayout
          channels={channels}
          activeSlug={activeSlug}
          activeChannel={activeChannel}
          track={nowPlaying}
          isPlaying={isPlaying}
          elapsedMs={elapsedMs}
          durationMs={durationMs}
          audioRef={audioRef}
          showChannelMenu={showChannelMenu}
          onTogglePlay={togglePlay}
          onLike={handleLike}
          onSelectChannel={handleSelectChannelBySlug}
          onChannelMenuToggle={() => setShowChannelMenu((v) => !v)}
          onShowManager={() => setCurrentScreen("manager")}
          liked={liked}
        />
      )}

      {/* Desktop layout */}
      {breakpoint === "desktop" && (
        <DesktopLayout
          channels={channels}
          activeSlug={activeSlug}
          activeChannel={activeChannel}
          track={nowPlaying}
          isPlaying={isPlaying}
          elapsedMs={elapsedMs}
          durationMs={durationMs}
          audioRef={audioRef}
          showLyricsPanel={showLyricsPanel}
          showChannelMenu={showChannelMenu}
          onTogglePlay={togglePlay}
          onLike={handleLike}
          onSelectChannel={handleSelectChannelBySlug}
          onLyricsPanelToggle={() => setShowLyricsPanel((v) => !v)}
          onChannelMenuToggle={() => setShowChannelMenu((v) => !v)}
          onShowManager={() => setCurrentScreen("manager")}
          liked={liked}
        />
      )}
    </div>
  );
}
