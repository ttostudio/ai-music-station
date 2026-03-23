import { useState, useEffect, useRef, useCallback } from "react";
import { ChannelManager } from "./components/ChannelManager";
import { ChannelSelector } from "./components/ChannelSelector";
import { MediaDisplay } from "./components/MediaDisplay";
import { NowPlaying } from "./components/NowPlaying";
import { Player } from "./components/Player";
import { RequestForm } from "./components/RequestForm";
import { TrackHistory } from "./components/TrackHistory";
import { TrackTitle } from "./components/TrackTitle";
import { useChannels } from "./hooks/useChannels";
import { useNowPlaying } from "./hooks/useNowPlaying";
import { useKeyboardShortcuts } from "./hooks/useKeyboardShortcuts";

export default function App() {
  const { channels, loading, error } = useChannels();
  const [activeSlug, setActiveSlug] = useState<string | null>(null);
  const playerRef = useRef<HTMLDivElement>(null);
  const [showManager, setShowManager] = useState(false);
  const [isPlaying, setIsPlaying] = useState(false);
  const [volume, setVolume] = useState(0.8);
  const prevVolumeRef = useRef(0.8);
  const nowPlaying = useNowPlaying(activeSlug);

  const handleChannelSelect = useCallback((slug: string) => {
    setActiveSlug(slug);
    // Ensure the player stays visible after new components render below
    requestAnimationFrame(() => {
      playerRef.current?.scrollIntoView({ behavior: "smooth", block: "nearest" });
    });
  }, []);

  const activeChannel = channels.find((c) => c.slug === activeSlug);
  const streamUrl = activeChannel ? activeChannel.stream_url : null;

  // Shared audioRef — passed to Player and MediaDisplay (AudioVisualizer)
  const audioRef = useRef<HTMLAudioElement>(null);

  const togglePlay = useCallback(async () => {
    if (!audioRef.current || !streamUrl) return;
    try {
      if (isPlaying) {
        audioRef.current.pause();
        setIsPlaying(false);
      } else {
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

  useKeyboardShortcuts({
    onTogglePlay: togglePlay,
    onVolumeUp: handleVolumeUp,
    onVolumeDown: handleVolumeDown,
    onMute: handleMute,
    onSelectChannel: handleSelectChannel,
  });

  // Track elapsed playback time for lyrics sync and ProgressRing
  const [elapsedMs, setElapsedMs] = useState(0);
  const trackIdRef = useRef<string | null>(null);

  useEffect(() => {
    if (!nowPlaying) {
      setElapsedMs(0);
      trackIdRef.current = null;
      return;
    }

    if (trackIdRef.current !== nowPlaying.id) {
      trackIdRef.current = nowPlaying.id;
      setElapsedMs(0);
    }

    const id = setInterval(() => {
      setElapsedMs((prev) => prev + 500);
    }, 500);

    return () => clearInterval(id);
  }, [nowPlaying]);

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-900 text-white flex items-center justify-center">
        <div className="text-gray-400">チャンネルを読み込み中...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-900 text-white flex items-center justify-center">
        <div className="text-red-400">{error}</div>
      </div>
    );
  }

  const durationMs = nowPlaying?.duration_ms ?? 0;

  // Determine ambient glow class from active channel
  const ambientClass = activeSlug
    ? activeSlug.includes("lofi") || activeSlug.includes("lo-fi") ? "ambient-lofi"
    : activeSlug.includes("anime") ? "ambient-anime"
    : activeSlug.includes("jazz") ? "ambient-jazz"
    : activeSlug.includes("game") ? "ambient-game"
    : ""
    : "";

  return (
    <div className="min-h-screen relative overflow-hidden" style={{ background: "var(--bg-primary)" }}>
      {/* Channel-aware ambient background glow */}
      <div className={`ambient-glow ${ambientClass}`} />

      <div className="relative z-10">
        {/* Header */}
        <header className="text-center pt-6 pb-2 slide-up px-4">
          <h1 className="text-4xl font-bold tracking-tight bg-gradient-to-r from-indigo-400 via-purple-400 to-pink-400 bg-clip-text text-transparent">
            AI Music Station
          </h1>
          <p className="mt-2" style={{ color: "var(--text-secondary)" }}>
            AIが生成した音楽をライブ配信
          </p>
          <button
            onClick={() => setShowManager((v) => !v)}
            className="mt-3 text-sm px-4 py-1.5 rounded-full focus-ring"
            style={{ color: "var(--text-secondary)", transition: "background-color var(--transition-normal) var(--ease-smooth)" }}
            onMouseOver={(e) => ((e.target as HTMLButtonElement).style.background = "rgba(255,255,255,0.1)")}
            onMouseOut={(e) => ((e.target as HTMLButtonElement).style.background = "")}
          >
            {showManager ? "← ラジオに戻る" : "⚙️ チャンネル管理"}
          </button>
        </header>

        {showManager ? (
          <div className="max-w-2xl mx-auto px-4 py-4">
            <ChannelManager onClose={() => setShowManager(false)} />
          </div>
        ) : (
          <div className="app-layout">
            {/* 左カラム */}
            <aside className="left-column">
              <ChannelSelector
                channels={channels}
                activeSlug={activeSlug}
                onSelect={handleChannelSelect}
              />

              <div ref={playerRef}>
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

              {activeSlug && (
                <div className="space-y-5 slide-up">
                  <NowPlaying track={nowPlaying} activeSlug={activeSlug} />
                  {nowPlaying && <TrackTitle track={nowPlaying} />}
                  <RequestForm channelSlug={activeSlug} />
                  <TrackHistory channelSlug={activeSlug} nowPlayingId={nowPlaying?.id} />
                </div>
              )}

              <footer className="text-center text-xs pt-4 pb-2 space-y-1" style={{ color: "var(--text-muted)" }}>
                <div className="shortcut-hints">
                  <span>Space 再生/停止</span>
                  <span>M ミュート</span>
                  <span>&uarr;&darr; 音量</span>
                  <span>1-9 CH切替</span>
                </div>
                <div>AI Music Station &mdash; ACE-Step v1.5 搭載</div>
              </footer>
            </aside>

            {/* 右カラム */}
            <main className="right-column">
              <MediaDisplay
                audioRef={audioRef}
                isPlaying={isPlaying}
                channelSlug={activeSlug}
                lyrics={nowPlaying?.lyrics}
                elapsedMs={elapsedMs}
                durationMs={durationMs}
              />
            </main>
          </div>
        )}
      </div>
    </div>
  );
}
