import type { Track } from "../api/types";

interface Props {
  track: Track;
}

export function TrackTitle({ track }: Props) {
  const displayTitle = track.title || track.caption;

  return (
    <div className="text-center py-3">
      <h2 className="text-2xl font-bold bg-gradient-to-r from-white via-gray-200 to-gray-400 bg-clip-text text-transparent">
        {displayTitle}
      </h2>
      {track.mood && (
        <p className="text-sm mt-1.5" style={{ color: 'var(--text-secondary)' }}>{track.mood}</p>
      )}
      {track.instrumental && (
        <p className="text-sm text-indigo-400 mt-1.5">🎵 インスト楽曲</p>
      )}
    </div>
  );
}
