import { useEffect, useRef, useState } from "react";
import type { Track } from "../api/types";

interface Props {
  streamUrl: string | null;
  channelName: string;
  nowPlaying?: Track | null;
}

function VisualizerBars({ playing }: { playing: boolean }) {
  if (!playing) return null;

  const bars = Array.from({ length: 5 }, (_, i) => i);
  return (
    <div className="visualizer">
      {bars.map((i) => (
        <div
          key={i}
          className="visualizer-bar"
          style={{
            animationDelay: `${i * 0.15}s`,
            ["--duration" as string]: `${0.6 + i * 0.1}s`,
          }}
        />
      ))}
    </div>
  );
}

export function Player({ streamUrl, channelName, nowPlaying }: Props) {
  const audioRef = useRef<HTMLAudioElement>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [volume, setVolume] = useState(0.8);

  useEffect(() => {
    if (audioRef.current) {
      audioRef.current.volume = volume;
    }
  }, [volume]);

  useEffect(() => {
    if (audioRef.current && streamUrl) {
      audioRef.current.load();
      if (isPlaying) {
        audioRef.current.play().catch(() => setIsPlaying(false));
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [streamUrl]);

  const togglePlay = () => {
    if (!audioRef.current || !streamUrl) return;

    if (isPlaying) {
      audioRef.current.pause();
      setIsPlaying(false);
    } else {
      audioRef.current.play().catch(() => setIsPlaying(false));
      setIsPlaying(true);
    }
  };

  return (
    <div className={`glass-card p-6 slide-up ${isPlaying ? "glow-accent" : ""}`}>
      <audio ref={audioRef} src={streamUrl ?? undefined} preload="none" />

      <div className="flex items-center gap-5">
        {/* Play/Pause Button */}
        <button
          onClick={togglePlay}
          disabled={!streamUrl}
          className={`w-16 h-16 rounded-full flex items-center justify-center transition-all duration-300 ${
            isPlaying
              ? "bg-gradient-to-br from-indigo-500 to-purple-600 shadow-lg shadow-indigo-500/30 hover:shadow-indigo-500/50"
              : streamUrl
                ? "bg-white/10 hover:bg-white/15 hover:scale-105"
                : "bg-white/5 opacity-50 cursor-not-allowed"
          }`}
          aria-label={isPlaying ? "一時停止" : "再生"}
        >
          {isPlaying ? (
            <svg className="w-6 h-6 text-white" fill="currentColor" viewBox="0 0 24 24">
              <rect x="6" y="5" width="4" height="14" rx="1" />
              <rect x="14" y="5" width="4" height="14" rx="1" />
            </svg>
          ) : (
            <svg className="w-6 h-6 ml-1 text-white" fill="currentColor" viewBox="0 0 24 24">
              <path d="M8 5v14l11-7z" />
            </svg>
          )}
        </button>

        {/* Channel Info + Visualizer */}
        <div className="flex-1 min-w-0">
          <div className="text-xs uppercase tracking-widest" style={{ color: 'var(--text-muted)' }}>
            ストリーミング中
          </div>
          <div className="text-lg font-bold truncate mt-0.5">
            {channelName || "チャンネルを選択してください"}
          </div>
          {nowPlaying && (
            <div className="text-sm truncate mt-0.5" style={{ color: 'var(--text-secondary)' }}>
              {nowPlaying.title || nowPlaying.caption}
            </div>
          )}
        </div>

        {/* Visualizer */}
        <VisualizerBars playing={isPlaying} />

        {/* Volume Control */}
        <div className="flex items-center gap-2">
          <svg className="w-5 h-5 shrink-0" style={{ color: 'var(--text-secondary)' }} fill="currentColor" viewBox="0 0 24 24">
            <path d="M3 9v6h4l5 5V4L7 9H3zm13.5 3c0-1.77-1.02-3.29-2.5-4.03v8.05c1.48-.73 2.5-2.25 2.5-4.02z" />
          </svg>
          <input
            type="range"
            min="0"
            max="1"
            step="0.05"
            value={volume}
            onChange={(e) => setVolume(parseFloat(e.target.value))}
            className="w-24"
            aria-label="音量"
          />
        </div>
      </div>

      {/* Playing indicator line */}
      {isPlaying && (
        <div className="mt-4 h-0.5 rounded-full overflow-hidden bg-white/5">
          <div className="h-full rounded-full bg-gradient-to-r from-indigo-500 via-purple-500 to-pink-500 progress-glow"
            style={{ width: "100%", animation: "shimmer 3s linear infinite", backgroundSize: "200% 100%" }}
          />
        </div>
      )}
    </div>
  );
}
