import { useState } from "react";
import { Share2, Check } from "lucide-react";
import { createShareLink } from "../api/client";

interface Props {
  trackId: string | null;
  size?: number;
  color?: string;
  className?: string;
}

export function ShareButton({ trackId, size = 24, color = "#8B8BA0", className = "" }: Props) {
  const [copied, setCopied] = useState(false);
  const [loading, setLoading] = useState(false);

  const handleShare = async () => {
    if (!trackId || loading) return;
    setLoading(true);
    try {
      const result = await createShareLink(trackId);
      const { share_url } = result;

      if (navigator.share) {
        await navigator.share({ url: share_url, title: "AI Music Station" });
      } else {
        await navigator.clipboard.writeText(share_url);
      }

      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // ignore AbortError from navigator.share cancel
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={`share-button-wrapper ${className}`} style={{ position: "relative", display: "inline-flex" }}>
      <button
        className="action-btn"
        onClick={handleShare}
        aria-label="シェア"
        disabled={!trackId || loading}
      >
        {copied
          ? <Check size={size} color="#22c55e" />
          : <Share2 size={size} color={loading ? "#555" : color} />
        }
      </button>
      {copied && (
        <div className="share-toast" role="status" aria-live="polite">
          リンクをコピーしました
        </div>
      )}
    </div>
  );
}
