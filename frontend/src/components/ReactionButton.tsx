import { useState, useEffect, useCallback } from "react";
import { addReaction, removeReaction, getReaction } from "../api/client";

function getSessionId(): string {
  const key = "ams_session_id";
  try {
    let id = window.localStorage.getItem(key);
    if (!id) {
      id = crypto.randomUUID();
      window.localStorage.setItem(key, id);
    }
    return id;
  } catch {
    return crypto.randomUUID();
  }
}

interface Props {
  trackId: string;
}

export function ReactionButton({ trackId }: Props) {
  const [liked, setLiked] = useState(false);
  const [count, setCount] = useState(0);
  const [loading, setLoading] = useState(false);
  const [animating, setAnimating] = useState(false);

  const sessionId = getSessionId();

  const fetchStatus = useCallback(async () => {
    try {
      const data = await getReaction(trackId, sessionId);
      setLiked(data.user_reacted);
      setCount(data.count);
    } catch {
      // API not available yet — ignore
    }
  }, [trackId, sessionId]);

  useEffect(() => {
    fetchStatus();
  }, [fetchStatus]);

  const handleClick = async () => {
    if (loading) return;
    setLoading(true);
    setAnimating(true);

    // Reset animation
    setTimeout(() => setAnimating(false), 400);

    try {
      if (liked) {
        const res = await removeReaction(trackId, sessionId);
        setCount(res.count);
        setLiked(false);
      } else {
        const res = await addReaction(trackId, sessionId);
        setCount(res.count);
        setLiked(true);
      }
    } catch {
      // API not available yet — ignore
    } finally {
      setLoading(false);
    }
  };

  return (
    <button
      type="button"
      onClick={handleClick}
      disabled={loading}
      aria-label={liked ? "いいね解除" : "いいね"}
      className={`inline-flex items-center gap-2 px-4 py-2 rounded-full text-sm font-medium transition-all duration-300 ${
        liked
          ? "bg-gradient-to-r from-indigo-500 to-purple-600 text-white shadow-lg shadow-indigo-500/25"
          : "bg-white/5 border border-white/10 text-gray-300 hover:bg-white/10 hover:border-white/20"
      } disabled:opacity-50 ${animating ? "reaction-pop" : ""}`}
    >
      <span className={`text-base ${liked ? "scale-110" : ""} transition-transform`}>👍</span>
      {count > 0 && (
        <span className="tabular-nums">{count}</span>
      )}
    </button>
  );
}
