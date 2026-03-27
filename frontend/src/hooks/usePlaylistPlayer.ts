import { useState, useCallback, useRef, useEffect } from "react";
import type { Track } from "../api/types";
import { resumeAudioContext } from "../components/AudioVisualizer";

export type PlayMode = "stream" | "track";
export type RepeatMode = "off" | "one" | "all";

export interface PlaylistPlayerResult {
  playMode: PlayMode;
  trackQueue: Track[];
  currentTrackIndex: number;
  currentTrack: Track | null;
  shuffle: boolean;
  repeat: RepeatMode;
  isTrackPlaying: boolean;
  trackElapsedMs: number;
  trackDurationMs: number;
  playTrack: (track: Track, queue?: Track[]) => void;
  playPlaylist: (tracks: Track[], startIndex?: number) => void;
  nextTrack: () => void;
  prevTrack: () => void;
  toggleShuffle: () => void;
  cycleRepeat: () => void;
  switchToStream: () => void;
  switchToTrack: () => void;
  seekTo: (ratio: number) => void;
}

function buildShuffleOrder(length: number, currentIndex: number): number[] {
  const arr = Array.from({ length }, (_, i) => i);
  // Fisher-Yates shuffle
  for (let i = arr.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [arr[i], arr[j]] = [arr[j], arr[i]];
  }
  // Move currentIndex to front
  const pos = arr.indexOf(currentIndex);
  if (pos > 0) [arr[0], arr[pos]] = [arr[pos], arr[0]];
  return arr;
}

export function usePlaylistPlayer(
  trackAudioRef: React.RefObject<HTMLAudioElement | null>,
  onSwitchMode: (mode: PlayMode) => void,
  getAudioUrl: (trackId: string) => string,
): PlaylistPlayerResult {
  const [playMode, setPlayMode] = useState<PlayMode>("stream");
  const [trackQueue, setTrackQueue] = useState<Track[]>([]);
  const [currentTrackIndex, setCurrentTrackIndex] = useState(0);
  const [shuffle, setShuffle] = useState(false);
  const [repeat, setRepeat] = useState<RepeatMode>("off");
  const [isTrackPlaying, setIsTrackPlaying] = useState(false);
  const [trackElapsedMs, setTrackElapsedMs] = useState(0);
  const [trackDurationMs, setTrackDurationMs] = useState(0);

  // Mutable refs to avoid stale closures in event handlers
  const internalRef = useRef({
    trackQueue: [] as Track[],
    currentTrackIndex: 0,
    shuffle: false,
    repeat: "off" as RepeatMode,
    shuffleOrder: [] as number[],
    shufflePosition: 0,
  });

  // Keep internal ref in sync
  internalRef.current.trackQueue = trackQueue;
  internalRef.current.currentTrackIndex = currentTrackIndex;
  internalRef.current.shuffle = shuffle;
  internalRef.current.repeat = repeat;

  const loadAndPlay = useCallback(
    (index: number, queue: Track[]) => {
      const audio = trackAudioRef.current;
      if (!audio || !queue[index]) return;
      audio.src = getAudioUrl(queue[index].id);
      audio.load();
      audio.play().catch(() => setIsTrackPlaying(false));
    },
    [trackAudioRef, getAudioUrl],
  );

  const handleEnded = useCallback(() => {
    const { trackQueue: queue, currentTrackIndex: idx, shuffle: sh, repeat: rep, shuffleOrder, shufflePosition } =
      internalRef.current;

    if (rep === "one") {
      const audio = trackAudioRef.current;
      if (audio) {
        audio.currentTime = 0;
        audio.play().catch(() => {});
      }
      return;
    }

    if (sh) {
      const nextPos = shufflePosition + 1;
      if (nextPos >= shuffleOrder.length) {
        if (rep === "all") {
          const newOrder = buildShuffleOrder(queue.length, 0);
          internalRef.current.shuffleOrder = newOrder;
          internalRef.current.shufflePosition = 0;
          const nextIdx = newOrder[0];
          setCurrentTrackIndex(nextIdx);
          internalRef.current.currentTrackIndex = nextIdx;
          loadAndPlay(nextIdx, queue);
        } else {
          setIsTrackPlaying(false);
        }
      } else {
        internalRef.current.shufflePosition = nextPos;
        const nextIdx = shuffleOrder[nextPos];
        setCurrentTrackIndex(nextIdx);
        internalRef.current.currentTrackIndex = nextIdx;
        loadAndPlay(nextIdx, queue);
      }
    } else {
      const nextIdx = idx + 1;
      if (nextIdx >= queue.length) {
        if (rep === "all") {
          setCurrentTrackIndex(0);
          internalRef.current.currentTrackIndex = 0;
          loadAndPlay(0, queue);
        } else {
          setIsTrackPlaying(false);
        }
      } else {
        setCurrentTrackIndex(nextIdx);
        internalRef.current.currentTrackIndex = nextIdx;
        loadAndPlay(nextIdx, queue);
      }
    }
  }, [trackAudioRef, loadAndPlay]);

  // Attach audio event listeners
  useEffect(() => {
    const audio = trackAudioRef.current;
    if (!audio) return;

    const onTimeUpdate = () => setTrackElapsedMs((audio.currentTime || 0) * 1000);
    const onDurationChange = () => setTrackDurationMs((audio.duration || 0) * 1000);
    const onPlay = () => setIsTrackPlaying(true);
    const onPause = () => setIsTrackPlaying(false);

    audio.addEventListener("timeupdate", onTimeUpdate);
    audio.addEventListener("durationchange", onDurationChange);
    audio.addEventListener("ended", handleEnded);
    audio.addEventListener("play", onPlay);
    audio.addEventListener("pause", onPause);

    return () => {
      audio.removeEventListener("timeupdate", onTimeUpdate);
      audio.removeEventListener("durationchange", onDurationChange);
      audio.removeEventListener("ended", handleEnded);
      audio.removeEventListener("play", onPlay);
      audio.removeEventListener("pause", onPause);
    };
  }, [trackAudioRef, handleEnded]);

  const playTrack = useCallback(
    (track: Track, queue?: Track[]) => {
      const newQueue = queue ?? [track];
      const idx = newQueue.findIndex((t) => t.id === track.id);
      const safeIdx = idx >= 0 ? idx : 0;

      setTrackQueue(newQueue);
      setCurrentTrackIndex(safeIdx);
      internalRef.current.trackQueue = newQueue;
      internalRef.current.currentTrackIndex = safeIdx;
      setTrackElapsedMs(0);

      if (internalRef.current.shuffle) {
        const order = buildShuffleOrder(newQueue.length, safeIdx);
        internalRef.current.shuffleOrder = order;
        internalRef.current.shufflePosition = 0;
      }

      setPlayMode("track");
      onSwitchMode("track");

      const audio = trackAudioRef.current;
      if (audio) resumeAudioContext(audio);
      loadAndPlay(safeIdx, newQueue);
    },
    [loadAndPlay, onSwitchMode, trackAudioRef],
  );

  const playPlaylist = useCallback(
    (tracks: Track[], startIndex = 0) => {
      if (tracks.length === 0) return;
      const safeIdx = Math.min(startIndex, tracks.length - 1);

      setTrackQueue(tracks);
      setCurrentTrackIndex(safeIdx);
      internalRef.current.trackQueue = tracks;
      internalRef.current.currentTrackIndex = safeIdx;
      setTrackElapsedMs(0);

      if (internalRef.current.shuffle) {
        const order = buildShuffleOrder(tracks.length, safeIdx);
        internalRef.current.shuffleOrder = order;
        internalRef.current.shufflePosition = 0;
      }

      setPlayMode("track");
      onSwitchMode("track");

      const audio = trackAudioRef.current;
      if (audio) resumeAudioContext(audio);
      loadAndPlay(safeIdx, tracks);
    },
    [loadAndPlay, onSwitchMode, trackAudioRef],
  );

  const nextTrack = useCallback(() => {
    const { trackQueue: queue, currentTrackIndex: idx, shuffle: sh, shuffleOrder, shufflePosition } =
      internalRef.current;
    if (queue.length === 0) return;

    let nextIdx: number;
    if (sh && shuffleOrder.length > 0) {
      const nextPos = (shufflePosition + 1) % shuffleOrder.length;
      internalRef.current.shufflePosition = nextPos;
      nextIdx = shuffleOrder[nextPos];
    } else {
      nextIdx = (idx + 1) % queue.length;
    }

    setCurrentTrackIndex(nextIdx);
    internalRef.current.currentTrackIndex = nextIdx;
    setTrackElapsedMs(0);
    loadAndPlay(nextIdx, queue);
  }, [loadAndPlay]);

  const prevTrack = useCallback(() => {
    const audio = trackAudioRef.current;
    if (audio && audio.currentTime > 3) {
      audio.currentTime = 0;
      return;
    }

    const { trackQueue: queue, currentTrackIndex: idx, shuffle: sh, shuffleOrder, shufflePosition } =
      internalRef.current;
    if (queue.length === 0) return;

    let prevIdx: number;
    if (sh && shuffleOrder.length > 0) {
      const prevPos = (shufflePosition - 1 + shuffleOrder.length) % shuffleOrder.length;
      internalRef.current.shufflePosition = prevPos;
      prevIdx = shuffleOrder[prevPos];
    } else {
      prevIdx = (idx - 1 + queue.length) % queue.length;
    }

    setCurrentTrackIndex(prevIdx);
    internalRef.current.currentTrackIndex = prevIdx;
    setTrackElapsedMs(0);
    loadAndPlay(prevIdx, queue);
  }, [loadAndPlay, trackAudioRef]);

  const toggleShuffle = useCallback(() => {
    setShuffle((prev) => {
      const newShuffle = !prev;
      internalRef.current.shuffle = newShuffle;
      if (newShuffle && internalRef.current.trackQueue.length > 0) {
        const order = buildShuffleOrder(
          internalRef.current.trackQueue.length,
          internalRef.current.currentTrackIndex,
        );
        internalRef.current.shuffleOrder = order;
        internalRef.current.shufflePosition = 0;
      }
      return newShuffle;
    });
  }, []);

  const cycleRepeat = useCallback(() => {
    setRepeat((prev) => {
      const next: RepeatMode = prev === "off" ? "all" : prev === "all" ? "one" : "off";
      internalRef.current.repeat = next;
      return next;
    });
  }, []);

  const switchToStream = useCallback(() => {
    const audio = trackAudioRef.current;
    if (audio) audio.pause();
    setIsTrackPlaying(false);
    setPlayMode("stream");
    onSwitchMode("stream");
  }, [trackAudioRef, onSwitchMode]);

  const switchToTrack = useCallback(() => {
    setPlayMode("track");
    onSwitchMode("track");
  }, [onSwitchMode]);

  const seekTo = useCallback(
    (ratio: number) => {
      const audio = trackAudioRef.current;
      if (audio && audio.duration && isFinite(audio.duration)) {
        audio.currentTime = ratio * audio.duration;
      }
    },
    [trackAudioRef],
  );

  const currentTrack = trackQueue[currentTrackIndex] ?? null;

  return {
    playMode,
    trackQueue,
    currentTrackIndex,
    currentTrack,
    shuffle,
    repeat,
    isTrackPlaying,
    trackElapsedMs,
    trackDurationMs,
    playTrack,
    playPlaylist,
    nextTrack,
    prevTrack,
    toggleShuffle,
    cycleRepeat,
    switchToStream,
    switchToTrack,
    seekTo,
  };
}
