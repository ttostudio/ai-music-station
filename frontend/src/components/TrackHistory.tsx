import { useEffect, useState } from "react";
import { getTracks } from "../api/client";
import type { Track } from "../api/types";

interface Props {
  channelSlug: string;
}

export function TrackHistory({ channelSlug }: Props) {
  const [tracks, setTracks] = useState<Track[]>([]);

  useEffect(() => {
    getTracks(channelSlug, 10)
      .then((data) => setTracks(data.tracks))
      .catch(() => setTracks([]));
  }, [channelSlug]);

  if (tracks.length === 0) {
    return (
      <div className="text-gray-500 text-sm text-center py-2">
        このチャンネルにはまだトラックがありません。
      </div>
    );
  }

  return (
    <div className="space-y-2">
      <div className="text-sm font-medium text-gray-300">最近のトラック</div>
      {tracks.map((track) => (
        <div
          key={track.id}
          className="bg-gray-800 rounded px-3 py-2 text-sm flex justify-between"
        >
          <span className="truncate flex-1">{track.title || track.caption}</span>
          <span className="text-gray-500 ml-2 shrink-0">
            👍{track.like_count ?? 0} / {track.play_count}回再生
          </span>
        </div>
      ))}
    </div>
  );
}
