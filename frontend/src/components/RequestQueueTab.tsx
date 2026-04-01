import { useEffect, useState } from "react";
import { getAllRequests } from "../api/client";
import type { RequestDetailResponse } from "../api/types";
import { Inbox } from "lucide-react";
import { RequestVoteButton } from "./RequestVoteButton";
import { ChannelRanking } from "./ChannelRanking";

const STATUS_LABEL: Record<string, string> = {
  pending: "待機中",
  processing: "生成中",
  completed: "完了",
  failed: "失敗",
};

const STATUS_CLASS: Record<string, string> = {
  pending: "status-badge-pending",
  processing: "status-badge-processing",
  completed: "status-badge-completed",
  failed: "status-badge-failed",
};

function formatTime(dateStr: string): string {
  try {
    const d = new Date(dateStr);
    return d.toLocaleTimeString("ja-JP", { hour: "2-digit", minute: "2-digit" });
  } catch {
    return "--:--";
  }
}

function sortRequests(requests: RequestDetailResponse[]): RequestDetailResponse[] {
  return [...requests].sort((a, b) => {
    // pending を投票数 DESC → created_at ASC でソート
    if (a.status === "pending" && b.status === "pending") {
      if (b.vote_count !== a.vote_count) return b.vote_count - a.vote_count;
      return new Date(a.created_at).getTime() - new Date(b.created_at).getTime();
    }
    // pending を先頭に
    if (a.status === "pending") return -1;
    if (b.status === "pending") return 1;
    return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
  });
}

export function RequestQueueTab() {
  const [requests, setRequests] = useState<RequestDetailResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;

    const poll = async () => {
      try {
        const res = await getAllRequests(50);
        if (mounted) {
          setRequests(res.requests);
          setError(null);
        }
      } catch {
        if (mounted) setError("リクエストの取得に失敗しました");
      } finally {
        if (mounted) setLoading(false);
      }
    };

    poll();
    const interval = setInterval(poll, 5000);
    return () => {
      mounted = false;
      clearInterval(interval);
    };
  }, []);

  // 表示用チャンネルスラッグ（pending リクエストがある最初のチャンネル）
  const rankingSlug =
    requests.find((r) => r.status === "pending")?.channel_slug ??
    requests[0]?.channel_slug ??
    null;

  if (loading) {
    return (
      <div className="queue-tab-screen">
        <div className="mobile-tab-header">
          <Inbox size={20} />
          <span>リクエストキュー</span>
        </div>
        <div className="mobile-empty-state">読み込み中...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="queue-tab-screen">
        <div className="mobile-tab-header">
          <Inbox size={20} />
          <span>リクエストキュー</span>
        </div>
        <div className="mobile-empty-state" style={{ color: "#f87171" }}>{error}</div>
      </div>
    );
  }

  const sorted = sortRequests(requests);

  return (
    <div className="queue-tab-screen">
      <div className="mobile-tab-header">
        <Inbox size={20} />
        <span>リクエストキュー</span>
        {requests.length > 0 && (
          <span className="queue-tab-count">{requests.length}</span>
        )}
      </div>

      {sorted.length === 0 ? (
        <div className="mobile-empty-state">リクエストはありません</div>
      ) : (
        <div className="queue-tab-list">
          {sorted.map((req) => {
            const statusClass = STATUS_CLASS[req.status] ?? "status-badge-pending";
            const label = STATUS_LABEL[req.status] ?? req.status;

            return (
              <div key={req.id} className="queue-tab-item">
                <div className="queue-tab-item-info">
                  <div className="queue-tab-item-title">
                    {req.caption || req.mood || "リクエスト"}
                  </div>
                  <div className="queue-tab-item-meta">
                    <span>{req.channel_slug}</span>
                    {req.mood && req.caption && <span>{req.mood}</span>}
                    <span>{formatTime(req.created_at)}</span>
                  </div>
                </div>
                <div className="queue-tab-item-status">
                  {req.status === "pending" && (
                    <RequestVoteButton
                      requestId={req.id}
                      initialCount={req.vote_count}
                    />
                  )}
                  {req.status === "pending" && req.position != null && (
                    <span className="queue-tab-position">#{req.position}</span>
                  )}
                  <span
                    className={`status-badge ${statusClass} ${req.status === "processing" ? "status-badge-pulse" : ""}`}
                  >
                    {label}
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {rankingSlug && (
        <div className="queue-tab-ranking">
          <ChannelRanking channelSlug={rankingSlug} />
        </div>
      )}
    </div>
  );
}
