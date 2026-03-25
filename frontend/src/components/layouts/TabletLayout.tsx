import type { Channel, Track } from "../../api/types";
import { TheaterView } from "../TheaterView";
import { FloatingBar } from "../FloatingBar";
import { ChannelMenu } from "../ChannelMenu";
import { LyricsScrollPanel } from "../LyricsScrollPanel";
import { RequestForm } from "../RequestForm";

interface Props {
  channels: Channel[];
  activeSlug: string | null;
  activeChannel: Channel | undefined;
  track: Track | null;
  isPlaying: boolean;
  elapsedMs: number;
  durationMs: number;
  audioRef: React.RefObject<HTMLAudioElement | null>;
  showChannelMenu: boolean;
  onTogglePlay: () => void;
  onLike: () => void;
  onSelectChannel: (slug: string) => void;
  onChannelMenuToggle: () => void;
  onShowManager: () => void;
  liked?: boolean;
}

export function TabletLayout({
  channels,
  activeSlug,
  activeChannel,
  track,
  isPlaying,
  elapsedMs,
  durationMs,
  audioRef,
  showChannelMenu,
  onTogglePlay,
  onLike,
  onSelectChannel,
  onChannelMenuToggle,
  onShowManager,
  liked,
}: Props) {
  const channelName = activeChannel?.name ?? "";
  const lyrics = track?.lyrics ?? "";

  return (
    <div className="tablet-layout">
      {/* Upper theater half */}
      <div className="tablet-upper">
        <TheaterView
          audioRef={audioRef}
          isPlaying={isPlaying}
          channelSlug={activeSlug}
          lyrics={lyrics || undefined}
          elapsedMs={elapsedMs}
          durationMs={durationMs}
        />

        <div className="tablet-floating-bar-wrapper">
          <FloatingBar
            track={track}
            channelName={channelName}
            isPlaying={isPlaying}
            elapsedMs={elapsedMs}
            durationMs={durationMs}
            lyricsActive={false}
            onPlayPause={onTogglePlay}
            onLike={onLike}
            onLyricsToggle={() => {}}
            onChannelMenu={onChannelMenuToggle}
            liked={liked}
          />
          {showChannelMenu && (
            <ChannelMenu
              channels={channels}
              activeSlug={activeSlug}
              onSelect={onSelectChannel}
              onManage={onShowManager}
              onClose={onChannelMenuToggle}
            />
          )}
        </div>
      </div>

      {/* Lower: lyrics + request form */}
      <div className="tablet-lower">
        {lyrics ? (
          <LyricsScrollPanel lyrics={lyrics} elapsedMs={elapsedMs} durationMs={durationMs} variant="tablet" />
        ) : (
          <div className="tablet-no-lyrics">♪ インストゥルメンタル</div>
        )}
        <div className="px-4 pb-4">
          <RequestForm channels={channels} defaultSlug={activeSlug ?? undefined} />
        </div>
      </div>
    </div>
  );
}
