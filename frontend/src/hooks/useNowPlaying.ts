import { useEffect, useState } from "react";
import { getNowPlaying } from "../api/client";
import type { Track } from "../api/types";

export function useNowPlaying(slug: string | null, intervalMs = 5000) {
  const [track, setTrack] = useState<Track | null>(null);

  useEffect(() => {
    if (!slug) {
      setTrack(null);
      return;
    }

    let cancelled = false;

    const poll = async () => {
      try {
        const data = await getNowPlaying(slug);
        if (!cancelled) {
          setTrack(data.track);
        }
      } catch {
        // Silently fail — will retry on next interval
      }
    };

    poll();
    const id = setInterval(poll, intervalMs);

    return () => {
      cancelled = true;
      clearInterval(id);
    };
  }, [slug, intervalMs]);

  return track;
}
