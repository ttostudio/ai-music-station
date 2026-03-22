import type { Channel } from "../api/types";

interface Props {
  channels: Channel[];
  activeSlug: string | null;
  onSelect: (slug: string) => void;
}

function getChannelGradient(slug: string): string {
  if (slug.includes("lofi") || slug.includes("lo-fi")) return "channel-gradient-lofi";
  if (slug.includes("anime")) return "channel-gradient-anime";
  if (slug.includes("jazz")) return "channel-gradient-jazz";
  if (slug.includes("game")) return "channel-gradient-game";
  return "channel-gradient-default";
}

function getChannelIconGradient(slug: string): string {
  if (slug.includes("lofi") || slug.includes("lo-fi")) return "channel-icon-lofi";
  if (slug.includes("anime")) return "channel-icon-anime";
  if (slug.includes("jazz")) return "channel-icon-jazz";
  if (slug.includes("game")) return "channel-icon-game";
  return "channel-icon-default";
}

function getChannelIcon(slug: string): string {
  if (slug.includes("lofi") || slug.includes("lo-fi")) return "🎧";
  if (slug.includes("anime")) return "🎤";
  if (slug.includes("jazz")) return "🎷";
  if (slug.includes("game")) return "🎮";
  return "🎵";
}

export function ChannelSelector({ channels, activeSlug, onSelect }: Props) {
  const visibleChannels = channels.filter((c) => c.is_active);

  return (
    <div
      className="channel-card-grid slide-up"
      style={{
        display: "grid",
        gridTemplateColumns: `repeat(auto-fill, minmax(var(--card-channel-width, 160px), 1fr))`,
        gap: "var(--card-channel-gap, 1rem)",
      }}
      role="radiogroup"
      aria-label="チャンネル選択"
    >
      {visibleChannels.map((channel) => {
        const isActive = activeSlug === channel.slug;
        const gradientClass = getChannelGradient(channel.slug);
        const iconGradientClass = getChannelIconGradient(channel.slug);

        return (
          <button
            key={channel.slug}
            onClick={() => onSelect(channel.slug)}
            className={`channel-card focus-ring ${
              isActive ? `channel-card-active ${gradientClass}` : ""
            }`}
            role="radio"
            aria-checked={isActive}
            aria-label={`${channel.name}チャンネルを選択`}
          >
            {/* アイコン with channel gradient */}
            <div className={`channel-card-icon ${iconGradientClass}`} aria-hidden="true">
              <span>{getChannelIcon(channel.slug)}</span>
            </div>

            {/* チャンネル名 */}
            <div className="channel-card-name">{channel.name}</div>

            {/* メタデータ */}
            <div
              className="channel-card-meta"
              aria-label={`${channel.total_tracks}曲${channel.queue_depth > 0 ? `、${channel.queue_depth}件待ち` : ""}`}
            >
              {channel.total_tracks}曲
              {channel.queue_depth > 0 && ` · ${channel.queue_depth}件待ち`}
            </div>

            {/* アクティブインジケーター */}
            {isActive && (
              <span className="channel-card-active-dot" aria-hidden="true" />
            )}
          </button>
        );
      })}
    </div>
  );
}
