import { useCallback, useEffect, useState } from "react";
import { getChannels } from "../api/client";
import type { Channel } from "../api/types";

export function useChannels() {
  const [channels, setChannels] = useState<Channel[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    try {
      const data = await getChannels();
      setChannels(data.channels);
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load channels");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  return { channels, loading, error, refresh };
}
