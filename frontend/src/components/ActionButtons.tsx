import { Heart, Type, Share2 } from "lucide-react";

interface Props {
  liked?: boolean;
  onLike: () => void;
  onLyrics: () => void;
  onShare: () => void;
}

export function ActionButtons({ liked, onLike, onLyrics, onShare }: Props) {
  return (
    <div className="action-buttons">
      <button className="action-btn" onClick={onLike} aria-label={liked ? "いいね解除" : "いいね"}>
        <Heart size={24} fill={liked ? "#ec4899" : "none"} color={liked ? "#ec4899" : "#8B8BA0"} />
      </button>
      <button className="action-btn" onClick={onLyrics} aria-label="歌詞">
        <Type size={24} color="#8B8BA0" />
      </button>
      <button className="action-btn" onClick={onShare} aria-label="シェア">
        <Share2 size={24} color="#8B8BA0" />
      </button>
    </div>
  );
}
