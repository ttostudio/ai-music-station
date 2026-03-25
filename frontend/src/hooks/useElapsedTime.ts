import { useState, useEffect, type RefObject } from "react";

/**
 * audioRef.currentTime を requestAnimationFrame で追跡し、
 * 経過時間をミリ秒で返すフック。
 * バックグラウンドタブでは rAF が停止するため不要な更新を回避できる。
 */
export function useElapsedTime(
  audioRef: RefObject<HTMLAudioElement | null>,
  isPlaying: boolean,
): number {
  const [elapsedMs, setElapsedMs] = useState(0);

  useEffect(() => {
    if (!isPlaying) return;

    let rafId: number;

    const tick = () => {
      if (audioRef.current) {
        setElapsedMs(Math.round(audioRef.current.currentTime * 1000));
      }
      rafId = requestAnimationFrame(tick);
    };

    rafId = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(rafId);
  }, [isPlaying, audioRef]);

  return elapsedMs;
}
