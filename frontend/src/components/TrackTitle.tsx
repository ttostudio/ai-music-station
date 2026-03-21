import type { Track } from "../api/types";

interface Props {
  track: Track;
}

export function TrackTitle({ track }: Props) {
  const displayTitle = track.title || track.caption;

  return (
    <div className="text-center py-2">
      <h2 className="text-xl font-bold">{displayTitle}</h2>
      {track.mood && (
        <p className="text-sm text-gray-400 mt-1">{track.mood}</p>
      )}
      {track.instrumental && (
        <p className="text-sm text-indigo-400 mt-1">🎵 インスト楽曲</p>
      )}
    </div>
  );
}
