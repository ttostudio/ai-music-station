import { Heart, Type } from "lucide-react";
import { ShareButton } from "./ShareButton";

interface Props {
  liked?: boolean;
  trackId?: string | null;
  onLike: () => void;
  onLyrics: () => void;
}

export function ActionButtons({ liked, trackId, onLike, onLyrics }: Props) {
  return (
    <div className="action-buttons">
      <button className="action-btn" onClick={onLike} aria-label={liked ? "いいね解除" : "いいね"}>
        <Heart size={24} fill={liked ? "#ec4899" : "none"} color={liked ? "#ec4899" : "#8B8BA0"} />
      </button>
      <button className="action-btn" onClick={onLyrics} aria-label="歌詞">
        <Type size={24} color="#8B8BA0" />
      </button>
      <ShareButton trackId={trackId ?? null} size={24} />
    </div>
  );
}
