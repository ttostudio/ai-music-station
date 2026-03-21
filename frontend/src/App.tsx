import { useState } from "react";
import { ChannelSelector } from "./components/ChannelSelector";
import { NowPlaying } from "./components/NowPlaying";
import { Player } from "./components/Player";
import { RequestForm } from "./components/RequestForm";
import { TrackHistory } from "./components/TrackHistory";
import { useChannels } from "./hooks/useChannels";
import { useNowPlaying } from "./hooks/useNowPlaying";

export default function App() {
  const { channels, loading, error } = useChannels();
  const [activeSlug, setActiveSlug] = useState<string | null>(null);
  const nowPlaying = useNowPlaying(activeSlug);

  const activeChannel = channels.find((c) => c.slug === activeSlug);
  const streamUrl = activeChannel ? activeChannel.stream_url : null;

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-900 text-white flex items-center justify-center">
        <div className="text-gray-400">Loading channels...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-900 text-white flex items-center justify-center">
        <div className="text-red-400">{error}</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      <div className="max-w-2xl mx-auto px-4 py-8 space-y-6">
        <header className="text-center">
          <h1 className="text-3xl font-bold">AI Music Station</h1>
          <p className="text-gray-400 mt-1">
            AI-generated music, streaming live
          </p>
        </header>

        <ChannelSelector
          channels={channels}
          activeSlug={activeSlug}
          onSelect={setActiveSlug}
        />

        <Player
          streamUrl={streamUrl}
          channelName={activeChannel?.name ?? ""}
        />

        {activeSlug && (
          <>
            <NowPlaying track={nowPlaying} />
            <RequestForm channelSlug={activeSlug} />
            <TrackHistory channelSlug={activeSlug} />
          </>
        )}
      </div>
    </div>
  );
}
