import { useState, useEffect, useRef } from "react";
import { ChannelManager } from "./components/ChannelManager";
import { ChannelSelector } from "./components/ChannelSelector";
import { LyricsDisplay } from "./components/LyricsDisplay";
import { NowPlaying } from "./components/NowPlaying";
import { Player } from "./components/Player";
import { RequestForm } from "./components/RequestForm";
import { TrackHistory } from "./components/TrackHistory";
import { TrackTitle } from "./components/TrackTitle";
import { useChannels } from "./hooks/useChannels";
import { useNowPlaying } from "./hooks/useNowPlaying";

export default function App() {
  const { channels, loading, error } = useChannels();
  const [activeSlug, setActiveSlug] = useState<string | null>(null);
  const [showManager, setShowManager] = useState(false);
  const nowPlaying = useNowPlaying(activeSlug);

  const activeChannel = channels.find((c) => c.slug === activeSlug);
  const streamUrl = activeChannel ? activeChannel.stream_url : null;

  // Track elapsed playback time for lyrics sync
  const [elapsedMs, setElapsedMs] = useState(0);
  const trackIdRef = useRef<string | null>(null);

  useEffect(() => {
    if (!nowPlaying) {
      setElapsedMs(0);
      trackIdRef.current = null;
      return;
    }

    // Reset elapsed when track changes
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

  return (
    <div className="min-h-screen relative overflow-hidden" style={{ background: 'var(--bg-primary)' }}>
      {/* Ambient background glow */}
      <div className="ambient-glow" />

      <div className="relative z-10 max-w-2xl mx-auto px-4 py-8 space-y-6">
        {/* Header */}
        <header className="text-center slide-up">
          <h1 className="text-4xl font-bold tracking-tight bg-gradient-to-r from-indigo-400 via-purple-400 to-pink-400 bg-clip-text text-transparent">
            AI Music Station
          </h1>
          <p className="mt-2" style={{ color: 'var(--text-secondary)' }}>
            AIが生成した音楽をライブ配信
          </p>
          <button
            onClick={() => setShowManager((v) => !v)}
            className="mt-3 text-sm px-4 py-1.5 rounded-full transition-all duration-300 hover:bg-white/10"
            style={{ color: 'var(--text-secondary)' }}
          >
            {showManager ? "← ラジオに戻る" : "⚙️ チャンネル管理"}
          </button>
        </header>

        {showManager ? (
          <ChannelManager onClose={() => setShowManager(false)} />
        ) : (
        <>
        <ChannelSelector
          channels={channels}
          activeSlug={activeSlug}
          onSelect={setActiveSlug}
        />

        <Player
          streamUrl={streamUrl}
          channelName={activeChannel?.name ?? ""}
          nowPlaying={nowPlaying}
        />

        {activeSlug && (
          <div className="space-y-5 slide-up">
            <NowPlaying track={nowPlaying} activeSlug={activeSlug} />
            {nowPlaying && <TrackTitle track={nowPlaying} />}
            {nowPlaying?.lyrics && (
              <LyricsDisplay
                lyrics={nowPlaying.lyrics}
                elapsedMs={elapsedMs}
                durationMs={nowPlaying.duration_ms ?? 0}
              />
            )}
            <RequestForm channelSlug={activeSlug} />
            <TrackHistory channelSlug={activeSlug} />
          </div>
        )}

        <footer className="text-center text-xs pt-4" style={{ color: 'var(--text-muted)' }}>
          AI Music Station &mdash; ACE-Step v1.5 搭載
        </footer>
        </>
        )}
      </div>
    </div>
  );
}
