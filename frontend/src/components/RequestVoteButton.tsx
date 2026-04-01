import { useState, useEffect, useCallback } from "react";
import { addRequestVote, removeRequestVote, getRequestVoteStatus } from "../api/client";
import { ThumbsUp } from "lucide-react";

function generateId(): string {
  if (typeof crypto !== "undefined" && typeof crypto.randomUUID === "function") {
    return crypto.randomUUID();
  }
  return "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx".replace(/[xy]/g, (c) => {
    const r = (Math.random() * 16) | 0;
    return (c === "x" ? r : (r & 0x3) | 0x8).toString(16);
  });
}

function getSessionId(): string {
  const key = "ams_session_id";
  try {
    let id = window.localStorage.getItem(key);
    if (!id) {
      id = generateId();
      window.localStorage.setItem(key, id);
    }
    return id;
  } catch {
    return generateId();
  }
}

interface Props {
  requestId: string;
  initialCount?: number;
}

export function RequestVoteButton({ requestId, initialCount = 0 }: Props) {
  const [voted, setVoted] = useState(false);
  const [count, setCount] = useState(initialCount);
  const [loading, setLoading] = useState(false);
  const [animating, setAnimating] = useState(false);

  const [sessionId] = useState(getSessionId);

  const fetchStatus = useCallback(async () => {
    try {
      const data = await getRequestVoteStatus(requestId, sessionId);
      setVoted(data.user_voted);
      setCount(data.count);
    } catch {
      // API not available yet — ignore
    }
  }, [requestId, sessionId]);

  useEffect(() => {
    fetchStatus();
  }, [fetchStatus]);

  const handleClick = async (e: React.MouseEvent) => {
    e.stopPropagation();
    if (loading) return;
    setLoading(true);
    setAnimating(true);
    setTimeout(() => setAnimating(false), 400);

    try {
      if (voted) {
        const res = await removeRequestVote(requestId, sessionId);
        setCount(res.count);
        setVoted(false);
      } else {
        const res = await addRequestVote(requestId, sessionId);
        setCount(res.count);
        setVoted(true);
      }
    } catch {
      // ignore
    } finally {
      setLoading(false);
    }
  };

  return (
    <button
      type="button"
      onClick={handleClick}
      disabled={loading}
      aria-label={voted ? "投票取消" : "投票する"}
      className={`request-vote-btn ${voted ? "request-vote-btn--voted" : ""} ${animating ? "reaction-pop" : ""}`}
    >
      <ThumbsUp size={13} />
      {count > 0 && <span className="request-vote-count">{count}</span>}
    </button>
  );
}
