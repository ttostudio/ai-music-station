import { useEffect, useState, useCallback } from "react";
import { getChannelRanking } from "../api/client";
import type { RankingTrack } from "../api/types";
import { Trophy, Heart } from "lucide-react";

const RANK_MEDALS = ["🥇", "🥈", "🥉", "4", "5"];

interface Props {
  channelSlug: string;
}

export function ChannelRanking({ channelSlug }: Props) {
  const [tracks, setTracks] = useState<RankingTrack[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchRanking = useCallback(async () => {
    try {
      const res = await getChannelRanking(channelSlug, 5);
      setTracks(res.tracks);
    } catch {
      // ignore
    } finally {
      setLoading(false);
    }
  }, [channelSlug]);

  useEffect(() => {
    fetchRanking();
    const interval = setInterval(fetchRanking, 30_000);
    return () => clearInterval(interval);
  }, [fetchRanking]);

  const likedTracks = tracks.filter((t) => t.like_count > 0);

  return (
    <div className="channel-ranking">
      <div className="channel-ranking-header">
        <Trophy size={16} />
        <span>人気楽曲ランキング</span>
        <span className="channel-ranking-slug">{channelSlug}</span>
      </div>

      {loading ? (
        <div className="channel-ranking-empty">読み込み中...</div>
      ) : likedTracks.length === 0 ? (
        <div className="channel-ranking-empty">まだランキングデータがありません</div>
      ) : (
        <ol className="channel-ranking-list">
          {tracks.slice(0, 5).map((track, i) => (
            <li key={track.id} className="channel-ranking-item">
              <span className="channel-ranking-medal">
                {i < 3 ? RANK_MEDALS[i] : `${i + 1}`}
              </span>
              <div className="channel-ranking-info">
                <div className="channel-ranking-title">
                  {track.title || track.caption}
                </div>
                {track.bpm && (
                  <div className="channel-ranking-meta">{track.bpm} BPM</div>
                )}
              </div>
              <div className="channel-ranking-likes">
                <Heart size={12} />
                <span>{track.like_count}</span>
              </div>
            </li>
          ))}
        </ol>
      )}
    </div>
  );
}
