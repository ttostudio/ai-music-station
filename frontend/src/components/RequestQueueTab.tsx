import { useEffect, useState } from "react";
import { getAllRequests } from "../api/client";
import type { RequestDetailResponse } from "../api/types";
import { Inbox } from "lucide-react";

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

  return (
    <div className="queue-tab-screen">
      <div className="mobile-tab-header">
        <Inbox size={20} />
        <span>リクエストキュー</span>
        {requests.length > 0 && (
          <span className="queue-tab-count">{requests.length}</span>
        )}
      </div>

      {requests.length === 0 ? (
        <div className="mobile-empty-state">リクエストはありません</div>
      ) : (
        <div className="queue-tab-list">
          {requests.map((req) => {
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
    </div>
  );
}
