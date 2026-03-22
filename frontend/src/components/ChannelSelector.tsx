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

export function ChannelSelector({ channels, activeSlug, onSelect }: Props) {
  return (
    <div className="flex gap-3 flex-wrap slide-up">
      {channels.map((channel) => {
        const isActive = activeSlug === channel.slug;
        const gradientClass = getChannelGradient(channel.slug);

        return (
          <button
            key={channel.slug}
            onClick={() => onSelect(channel.slug)}
            className={`group relative px-5 py-3 rounded-xl font-medium transition-all duration-300 overflow-hidden ${
              isActive
                ? `${gradientClass} text-white shadow-lg scale-105`
                : "glass-card-hover text-gray-300"
            }`}
          >
            {/* Active indicator dot */}
            {isActive && (
              <span className="absolute top-2 right-2 w-2 h-2 rounded-full bg-white/80 glow-pulse" />
            )}

            <span className="relative z-10">{channel.name}</span>
            {channel.queue_depth > 0 && (
              <span className="relative z-10 ml-2 text-xs opacity-70">
                ({channel.queue_depth}件待ち)
              </span>
            )}
          </button>
        );
      })}
    </div>
  );
}
