import type { Channel } from "../api/types";

interface Props {
  channels: Channel[];
  activeSlug: string | null;
  onSelect: (slug: string) => void;
}

export function ChannelSelector({ channels, activeSlug, onSelect }: Props) {
  return (
    <div className="flex gap-2 flex-wrap">
      {channels.map((channel) => (
        <button
          key={channel.slug}
          onClick={() => onSelect(channel.slug)}
          className={`px-4 py-2 rounded-lg font-medium transition-colors ${
            activeSlug === channel.slug
              ? "bg-indigo-600 text-white"
              : "bg-gray-700 text-gray-300 hover:bg-gray-600"
          }`}
        >
          <span>{channel.name}</span>
          {channel.queue_depth > 0 && (
            <span className="ml-2 text-xs opacity-70">
              ({channel.queue_depth} queued)
            </span>
          )}
        </button>
      ))}
    </div>
  );
}
