import type { Track } from "../api/types";
import { ReactionButton } from "./ReactionButton";

interface Props {
  track: Track | null;
}

export function NowPlaying({ track }: Props) {
  if (!track) {
    return (
      <div className="text-gray-500 text-center py-4">
        再生中のトラックはありません — リクエストを送信してください！
      </div>
    );
  }

  return (
    <div className="bg-gray-800 rounded-lg p-4">
      <div className="flex items-start justify-between">
        <div>
          <div className="text-sm text-gray-400 mb-1">再生中</div>
          <div className="font-medium">{track.caption}</div>
          <div className="flex gap-4 mt-2 text-sm text-gray-400">
            {track.bpm && <span>{track.bpm} BPM</span>}
            {track.music_key && <span>キー: {track.music_key}</span>}
            {track.duration_ms && (
              <span>{Math.round(track.duration_ms / 1000)}秒</span>
            )}
            {track.instrumental !== null && (
              <span>{track.instrumental ? "インスト" : "ボーカル"}</span>
            )}
          </div>
        </div>
        <ReactionButton trackId={track.id} />
      </div>
    </div>
  );
}
