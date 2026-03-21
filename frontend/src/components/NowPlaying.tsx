import type { Track } from "../api/types";

interface Props {
  track: Track | null;
}

export function NowPlaying({ track }: Props) {
  if (!track) {
    return (
      <div className="text-gray-500 text-center py-4">
        No track playing — submit a request to get started!
      </div>
    );
  }

  return (
    <div className="bg-gray-800 rounded-lg p-4">
      <div className="text-sm text-gray-400 mb-1">Now Playing</div>
      <div className="font-medium">{track.caption}</div>
      <div className="flex gap-4 mt-2 text-sm text-gray-400">
        {track.bpm && <span>{track.bpm} BPM</span>}
        {track.music_key && <span>Key: {track.music_key}</span>}
        {track.duration_ms && (
          <span>{Math.round(track.duration_ms / 1000)}s</span>
        )}
        {track.instrumental !== null && (
          <span>{track.instrumental ? "Instrumental" : "Vocal"}</span>
        )}
      </div>
    </div>
  );
}
