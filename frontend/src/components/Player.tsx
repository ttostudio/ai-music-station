import React, { useEffect, useRef, useState } from "react";
import type { Track } from "../api/types";

interface Props {
  streamUrl: string | null;
  channelName: string;
  nowPlaying?: Track | null;
  elapsedMs?: number;
  durationMs?: number;
  audioRef?: React.RefObject<HTMLAudioElement | null>;
  onPlayingChange?: (isPlaying: boolean) => void;
}

function getChannelGradient(name: string): string {
  const lower = name.toLowerCase();
  if (lower.includes("lofi") || lower.includes("lo-fi")) return "linear-gradient(135deg, #7c3aed, #a855f7)";
  if (lower.includes("anime")) return "linear-gradient(135deg, #ec4899, #f472b6)";
  if (lower.includes("jazz")) return "linear-gradient(135deg, #d97706, #fbbf24)";
  if (lower.includes("game")) return "linear-gradient(135deg, #059669, #34d399)";
  return "linear-gradient(135deg, #6366f1, #818cf8)";
}

const ProgressRing = React.memo(function ProgressRing({
  progress,
  size = 72,
  stroke = 3,
}: {
  progress: number;
  size?: number;
  stroke?: number;
}) {
  const radius = (size - stroke) / 2;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference * (1 - Math.min(progress, 1));

  return (
    <svg
      width={size}
      height={size}
      className="absolute inset-0"
      style={{ transform: "rotate(-90deg)" }}
      aria-hidden="true"
    >
      {/* Track */}
      <circle
        cx={size / 2}
        cy={size / 2}
        r={radius}
        fill="none"
        stroke="var(--ring-track-color)"
        strokeWidth={stroke}
      />
      {/* Progress */}
      <circle
        cx={size / 2}
        cy={size / 2}
        r={radius}
        fill="none"
        stroke="var(--ring-fill-color)"
        strokeWidth={stroke}
        strokeDasharray={circumference}
        strokeDashoffset={offset}
        strokeLinecap="round"
        style={{ transition: "stroke-dashoffset 0.5s ease" }}
      />
    </svg>
  );
});

export function Player({
  streamUrl,
  channelName,
  nowPlaying,
  elapsedMs = 0,
  durationMs = 0,
  audioRef: externalAudioRef,
  onPlayingChange,
}: Props) {
  const internalAudioRef = useRef<HTMLAudioElement>(null);
  const audioRef = externalAudioRef ?? internalAudioRef;
  const [isPlaying, setIsPlaying] = useState(false);
  const [volume, setVolume] = useState(0.8);

  const progress = durationMs > 0 ? Math.min(elapsedMs / durationMs, 1) : 0;

  useEffect(() => {
    if (audioRef.current) {
      audioRef.current.volume = volume;
    }
  }, [volume, audioRef]);

  useEffect(() => {
    if (audioRef.current && streamUrl) {
      audioRef.current.load();
      if (isPlaying) {
        audioRef.current.play().catch(() => {
          setIsPlaying(false);
          onPlayingChange?.(false);
        });
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [streamUrl]);

  const togglePlay = async () => {
    if (!audioRef.current || !streamUrl) return;
    try {
      if (isPlaying) {
        audioRef.current.pause();
        setIsPlaying(false);
        onPlayingChange?.(false);
      } else {
        await audioRef.current.play();
        setIsPlaying(true);
        onPlayingChange?.(true);
      }
    } catch {
      setIsPlaying(false);
      onPlayingChange?.(false);
    }
  };

  const ringSize = 72;
  const gradient = channelName ? getChannelGradient(channelName) : "linear-gradient(135deg, #6366f1, #818cf8)";
  const trackTitle = nowPlaying ? (nowPlaying.title || nowPlaying.caption) : null;

  return (
    <div className={`glass-card p-6 slide-up ${isPlaying ? "glow-accent" : ""}`}>
      <audio ref={audioRef} src={streamUrl ?? undefined} preload="none" />

      <div className="flex items-center gap-5">
        {/* Play/Pause button with ProgressRing */}
        <div
          className="relative shrink-0"
          style={{ width: ringSize, height: ringSize }}
        >
          <ProgressRing progress={progress} size={ringSize} stroke={3} />
          <button
            onClick={togglePlay}
            disabled={!streamUrl}
            className={`player-button focus-ring ${isPlaying ? "player-button-playing" : ""} ${!streamUrl ? "opacity-50 cursor-not-allowed" : ""}`}
            aria-label={isPlaying ? "一時停止" : "再生"}
          >
            {isPlaying ? (
              <svg className="w-6 h-6 text-white" fill="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                <rect x="6" y="5" width="4" height="14" rx="1" />
                <rect x="14" y="5" width="4" height="14" rx="1" />
              </svg>
            ) : (
              <svg className="w-6 h-6 ml-1 text-white" fill="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                <path d="M8 5v14l11-7z" />
              </svg>
            )}
          </button>
        </div>

        {/* Track info: 曲名大表示 */}
        <div className="flex-1 min-w-0">
          <div className="text-xs uppercase tracking-widest mb-1" style={{ color: "var(--text-muted)" }}>
            {channelName || "チャンネルを選択してください"}
          </div>
          {trackTitle ? (
            <div className="now-playing-title-wrapper">
              <span
                className="now-playing-title"
                style={{ backgroundImage: gradient }}
                title={trackTitle}
              >
                {trackTitle}
              </span>
            </div>
          ) : (
            <div className="text-sm" style={{ color: "var(--text-secondary)" }}>
              {streamUrl ? "再生を開始してください" : "チャンネルを選択して再生を開始してください"}
            </div>
          )}
        </div>

        {/* Volume Control */}
        <div className="flex items-center gap-2 volume-control shrink-0">
          <svg
            className="w-5 h-5 shrink-0"
            style={{ color: "var(--text-secondary)" }}
            fill="currentColor"
            viewBox="0 0 24 24"
            aria-hidden="true"
          >
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

      {/* Progress bar (実進捗 + shimmer) */}
      {isPlaying && (
        <div className="mt-4 h-0.5 rounded-full overflow-hidden bg-white/5">
          <div
            className="h-full rounded-full bg-gradient-to-r from-indigo-500 via-purple-500 to-pink-500"
            style={{
              width: `${progress * 100}%`,
              transition: "width 0.5s linear",
            }}
          />
        </div>
      )}
    </div>
  );
}
