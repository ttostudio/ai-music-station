import { useEffect, useState } from "react";
import { getGenerateStatus } from "../api/client";
import type { RequestDetailResponse } from "../api/types";

const STATUS_LABEL: Record<string, string> = {
  pending: "待機中",
  processing: "生成中",
  completed: "完了",
  failed: "失敗",
};

const STATUS_COLOR: Record<string, string> = {
  pending: "var(--text-muted)",
  processing: "#60a5fa",
  completed: "#4ade80",
  failed: "#f87171",
};

interface Props {
  requestIds: string[];
}

export function RequestHistory({ requestIds }: Props) {
  const [statuses, setStatuses] = useState<Record<string, RequestDetailResponse>>({});

  useEffect(() => {
    if (requestIds.length === 0) return;

    const pollPending = async () => {
      for (const id of requestIds) {
        const current = statuses[id];
        if (current?.status === "completed" || current?.status === "failed") continue;
        try {
          const detail = await getGenerateStatus(id);
          setStatuses((prev) => ({ ...prev, [id]: detail }));
        } catch {
          // Ignore fetch errors silently
        }
      }
    };

    pollPending();
    const interval = setInterval(pollPending, 5000);
    return () => clearInterval(interval);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [requestIds]);

  if (requestIds.length === 0) return null;

  return (
    <div className="glass-card p-4 mt-3 space-y-2">
      <div className="text-xs font-semibold mb-2" style={{ color: "var(--text-secondary)" }}>
        リクエスト履歴
      </div>
      {requestIds.map((id) => {
        const detail = statuses[id];
        const status = detail?.status ?? "pending";
        const position = detail?.position;
        const label = STATUS_LABEL[status] ?? status;
        const color = STATUS_COLOR[status] ?? "var(--text-muted)";

        return (
          <div
            key={id}
            className="flex items-center justify-between text-xs py-1.5 border-b border-white/5 last:border-0"
          >
            <div style={{ color: "var(--text-secondary)" }}>
              {detail?.caption ?? detail?.mood ?? "リクエスト中..."}
            </div>
            <div className="flex items-center gap-2">
              {status === "pending" && position != null && (
                <span style={{ color: "var(--text-muted)" }}>#{position}</span>
              )}
              <span
                className={`status-badge ${status === "processing" ? "status-badge-pulse" : ""}`}
                style={{ color }}
              >
                {label}
              </span>
            </div>
          </div>
        );
      })}
    </div>
  );
}
