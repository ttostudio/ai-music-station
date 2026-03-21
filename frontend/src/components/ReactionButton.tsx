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
      className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-sm font-medium transition-colors ${
        liked
          ? "bg-indigo-600 text-white"
          : "bg-gray-700 text-gray-300 hover:bg-gray-600"
      } disabled:opacity-50`}
    >
      <span>{liked ? "👍" : "👍"}</span>
      {count > 0 && <span>{count}</span>}
    </button>
  );
}
