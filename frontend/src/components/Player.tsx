import { useEffect, useRef, useState } from "react";

interface Props {
  streamUrl: string | null;
  channelName: string;
}

export function Player({ streamUrl, channelName }: Props) {
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
    <div className="bg-gray-800 rounded-xl p-6 flex items-center gap-6">
      <audio ref={audioRef} src={streamUrl ?? undefined} preload="none" />

      <button
        onClick={togglePlay}
        disabled={!streamUrl}
        className="w-14 h-14 rounded-full bg-indigo-600 hover:bg-indigo-500 disabled:bg-gray-600 flex items-center justify-center transition-colors"
        aria-label={isPlaying ? "Pause" : "Play"}
      >
        {isPlaying ? (
          <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 24 24">
            <rect x="6" y="5" width="4" height="14" rx="1" />
            <rect x="14" y="5" width="4" height="14" rx="1" />
          </svg>
        ) : (
          <svg className="w-6 h-6 ml-1" fill="currentColor" viewBox="0 0 24 24">
            <path d="M8 5v14l11-7z" />
          </svg>
        )}
      </button>

      <div className="flex-1">
        <div className="text-sm text-gray-400">Now streaming</div>
        <div className="text-lg font-semibold">{channelName || "Select a channel"}</div>
      </div>

      <div className="flex items-center gap-2">
        <svg className="w-5 h-5 text-gray-400" fill="currentColor" viewBox="0 0 24 24">
          <path d="M3 9v6h4l5 5V4L7 9H3zm13.5 3c0-1.77-1.02-3.29-2.5-4.03v8.05c1.48-.73 2.5-2.25 2.5-4.02z" />
        </svg>
        <input
          type="range"
          min="0"
          max="1"
          step="0.05"
          value={volume}
          onChange={(e) => setVolume(parseFloat(e.target.value))}
          className="w-24 accent-indigo-500"
          aria-label="Volume"
        />
      </div>
    </div>
  );
}
