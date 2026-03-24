import { Settings } from "lucide-react";
import type { Channel } from "../api/types";
import { getChannelGradient, getChannelThemeKey } from "../utils/lrc-parser";
import { useEffect, useRef } from "react";

interface Props {
  channels: Channel[];
  activeSlug: string | null;
  onSelect: (slug: string) => void;
  onManage: () => void;
  onClose: () => void;
}

function getChannelIcon(slug: string): string {
  if (slug.includes("anime")) return "\uD83C\uDFA4";
  if (slug.includes("egushi") || slug.includes("えぐ")) return "\uD83C\uDFB5";
  if (slug.includes("game")) return "\uD83C\uDFAE";
  if (slug.includes("jazz")) return "\uD83C\uDFB7";
  if (slug.includes("podcast")) return "\uD83C\uDFA7";
  return "\uD83C\uDFB5";
}

export function ChannelMenu({ channels, activeSlug, onSelect, onManage, onClose }: Props) {
  const menuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        onClose();
      }
    };
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    document.addEventListener("mousedown", handleClickOutside);
    document.addEventListener("keydown", handleEscape);
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
      document.removeEventListener("keydown", handleEscape);
    };
  }, [onClose]);

  const visibleChannels = channels.filter((c) => c.is_active);

  return (
    <div className="channel-menu" ref={menuRef} role="menu">
      <div className="channel-menu-header">
        <span>チャンネル</span>
        <button className="channel-menu-manage-btn" onClick={onManage} aria-label="チャンネル管理">
          <Settings size={16} />
        </button>
      </div>
      <div className="channel-menu-list">
        {visibleChannels.map((ch) => {
          const isActive = ch.slug === activeSlug;
          const themeKey = getChannelThemeKey(ch.slug);
          return (
            <button
              key={ch.slug}
              className={`channel-menu-item ${isActive ? `channel-active-${themeKey}` : ""}`}
              role="menuitem"
              onClick={() => { onSelect(ch.slug); onClose(); }}
            >
              <span className="channel-menu-icon" style={{ background: getChannelGradient(ch.slug) }}>
                {getChannelIcon(ch.slug)}
              </span>
              <span className="channel-menu-name">{ch.name}</span>
              <span className="channel-menu-count">{ch.total_tracks}曲</span>
            </button>
          );
        })}
      </div>
    </div>
  );
}
