import React, { useEffect, useRef } from "react";
import type { Track } from "../api/types";

interface Props {
  streamUrl: string | null;
  channelName: string;
  nowPlaying?: Track | null;
  elapsedMs?: number;
  durationMs?: number;
  audioRef?: React.RefObject<HTMLAudioElement | null>;
  onPlayingChange?: (isPlaying: boolean) => void;
  volume: number;
  onVolumeChange: (v: number) => void;
  isPlaying: boolean;
  onTogglePlay: () => void;
}

interface ChannelTheme {
  gradient: string;
  colors: [string, string, string];
}

function getChannelTheme(name: string): ChannelTheme {
  const lower = name.toLowerCase();
  if (lower.includes("lofi") || lower.includes("lo-fi"))
    return { gradient: "linear-gradient(135deg, #7c3aed, #a855f7)", colors: ["#7c3aed", "#a855f7", "#6d28d9"] };
  if (lower.includes("anime"))
    return { gradient: "linear-gradient(135deg, #ec4899, #f472b6)", colors: ["#ec4899", "#f472b6", "#db2777"] };
  if (lower.includes("jazz"))
    return { gradient: "linear-gradient(135deg, #d97706, #fbbf24)", colors: ["#d97706", "#fbbf24", "#b45309"] };
  if (lower.includes("game"))
    return { gradient: "linear-gradient(135deg, #059669, #34d399)", colors: ["#059669", "#34d399", "#047857"] };
  return { gradient: "linear-gradient(135deg, #6366f1, #818cf8)", colors: ["#6366f1", "#818cf8", "#4f46e5"] };
}


const ProgressRing = React.memo(function ProgressRing({
  progress,
  size = 72,
  stroke = 3,
  colors,
  isPlaying = false,
}: {
  progress: number;
  size?: number;
  stroke?: number;
  colors?: [string, string, string];
  isPlaying?: boolean;
}) {
  const radius = (size - stroke) / 2;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference * (1 - Math.min(progress, 1));
  const gradientId = "ring-gradient";

  return (
    <svg
      width={size}
      height={size}
      className={`absolute inset-0 ${isPlaying ? "progress-ring-glow-playing" : "progress-ring-glow"}`}
      style={{ transform: "rotate(-90deg)" }}
      aria-hidden="true"
    >
      <defs>
        <linearGradient id={gradientId} x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor={colors?.[0] ?? "var(--accent-primary)"} />
          <stop offset="50%" stopColor={colors?.[1] ?? "var(--accent-primary)"} />
          <stop offset="100%" stopColor={colors?.[2] ?? "var(--accent-primary)"} />
        </linearGradient>
      </defs>
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
        stroke={`url(#${gradientId})`}
        strokeWidth={isPlaying ? stroke + 1 : stroke}
        strokeDasharray={circumference}
        strokeDashoffset={offset}
        strokeLinecap="round"
        style={{ transition: "stroke-dashoffset 0.5s ease, stroke-width 0.3s ease" }}
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
  volume,
  onVolumeChange,
  isPlaying,
  onTogglePlay,
}: Props) {
  const internalAudioRef = useRef<HTMLAudioElement>(null);
  const audioRef = externalAudioRef ?? internalAudioRef;

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
          /* handled by parent */
        });
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [streamUrl]);

  const ringSize = 72;
  const theme = channelName ? getChannelTheme(channelName) : getChannelTheme("");
  const gradient = theme.gradient;
  const trackTitle = nowPlaying ? (nowPlaying.title || nowPlaying.caption) : null;

  return (
    <div className={`glass-card p-6 slide-up ${isPlaying ? "player-card-playing glow-accent" : ""}`}>
      <audio ref={audioRef} src={streamUrl ?? undefined} preload="none" />

      <div className="flex items-center gap-5">
        {/* Album art with Progress Ring */}
        <div
          className={`album-art ${isPlaying ? "album-art-playing" : ""}`}
          style={{ width: ringSize, height: ringSize }}
        >
          <ProgressRing progress={progress} size={ringSize} stroke={3} colors={theme.colors} isPlaying={isPlaying} />
          <div className="album-art-inner">
            <div
              className="album-art-visual"
              style={{
                background: `conic-gradient(from 0deg, ${theme.colors[0]}, ${theme.colors[1]}, ${theme.colors[2]}, ${theme.colors[0]})`,
              }}
            />
            <div className="album-art-center" />
          </div>
          <button
            onClick={onTogglePlay}
            disabled={!streamUrl}
            className={`player-button focus-ring ${isPlaying ? "player-button-playing" : ""} ${!streamUrl ? "opacity-50 cursor-not-allowed" : ""}`}
            style={{ position: "absolute", inset: 0, background: isPlaying ? "transparent" : undefined }}
            aria-label={isPlaying ? "一時停止" : "再生"}
          >
            {isPlaying ? (
              <svg className="w-6 h-6 text-white drop-shadow-lg" fill="currentColor" viewBox="0 0 24 24" aria-hidden="true">
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
            className="w-5 h-5 shrink-0 volume-icon-interactive"
            style={{ color: "var(--text-secondary)" }}
            fill="currentColor"
            viewBox="0 0 24 24"
            aria-hidden="true"
            onClick={() => onVolumeChange(volume > 0 ? 0 : 0.8)}
          >
            {volume === 0 ? (
              <path d="M16.5 12c0-1.77-1.02-3.29-2.5-4.03v2.21l2.45 2.45c.03-.2.05-.41.05-.63zm2.5 0c0 .94-.2 1.82-.54 2.64l1.51 1.51C20.63 14.91 21 13.5 21 12c0-4.28-2.99-7.86-7-8.77v2.06c2.89.86 5 3.54 5 6.71zM4.27 3L3 4.27 7.73 9H3v6h4l5 5v-6.73l4.25 4.25c-.67.52-1.42.93-2.25 1.18v2.06c1.38-.31 2.63-.95 3.69-1.81L19.73 21 21 19.73l-9-9L4.27 3zM12 4L9.91 6.09 12 8.18V4z" />
            ) : (
              <path d="M3 9v6h4l5 5V4L7 9H3zm13.5 3c0-1.77-1.02-3.29-2.5-4.03v8.05c1.48-.73 2.5-2.25 2.5-4.02z" />
            )}
          </svg>
          <input
            type="range"
            min="0"
            max="1"
            step="0.05"
            value={volume}
            onChange={(e) => onVolumeChange(parseFloat(e.target.value))}
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
