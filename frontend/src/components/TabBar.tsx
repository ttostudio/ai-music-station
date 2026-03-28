import { Radio, ListMusic, Heart, ListVideo, Inbox } from "lucide-react";

export type Tab = "radio" | "tracks" | "likes" | "playlist" | "queue";

interface Props {
  activeTab: Tab;
  onChange: (tab: Tab) => void;
  queueBadgeCount?: number;
}

const tabs = [
  { id: "radio" as const, label: "RADIO", Icon: Radio },
  { id: "tracks" as const, label: "TRACKS", Icon: ListMusic },
  { id: "likes" as const, label: "LIKES", Icon: Heart },
  { id: "playlist" as const, label: "PLAYLISTS", Icon: ListVideo },
  { id: "queue" as const, label: "QUEUE", Icon: Inbox },
];

export function TabBar({ activeTab, onChange, queueBadgeCount }: Props) {
  return (
    <div className="tabbar-outer" role="tablist" aria-label="ナビゲーション">
      <div className="tabbar-pill">
        {tabs.map(({ id, label, Icon }) => {
          const active = activeTab === id;
          return (
            <button
              key={id}
              role="tab"
              aria-selected={active}
              aria-controls={`panel-${id}`}
              className={`tabbar-item ${active ? "tabbar-item-active" : ""}`}
              onClick={() => onChange(id)}
            >
              <div className="tabbar-icon-wrapper">
                <Icon size={18} />
                {id === "queue" && queueBadgeCount != null && queueBadgeCount > 0 && (
                  <span className="tabbar-badge" aria-label={`${queueBadgeCount}件`}>
                    {queueBadgeCount > 9 ? "9+" : queueBadgeCount}
                  </span>
                )}
              </div>
              <span>{label}</span>
            </button>
          );
        })}
      </div>
    </div>
  );
}
