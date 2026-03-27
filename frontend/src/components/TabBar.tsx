import { Radio, ListMusic, Heart, ListVideo } from "lucide-react";

type Tab = "radio" | "tracks" | "likes" | "playlist";

interface Props {
  activeTab: Tab;
  onChange: (tab: Tab) => void;
}

const tabs = [
  { id: "radio" as const, label: "RADIO", Icon: Radio },
  { id: "tracks" as const, label: "TRACKS", Icon: ListMusic },
  { id: "likes" as const, label: "LIKES", Icon: Heart },
  { id: "playlist" as const, label: "PLAYLISTS", Icon: ListVideo },
];

export function TabBar({ activeTab, onChange }: Props) {
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
              <Icon size={18} />
              <span>{label}</span>
            </button>
          );
        })}
      </div>
    </div>
  );
}
