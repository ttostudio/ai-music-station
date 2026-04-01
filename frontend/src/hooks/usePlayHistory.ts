import { useState, useCallback } from "react";
import type { Track } from "../api/types";

const STORAGE_KEY = "ai-music-station:history";
const MAX_HISTORY = 20;

export interface HistoryEntry {
  track: Track;
  playedAt: string; // ISO8601
}

function loadHistory(): HistoryEntry[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return [];
    return JSON.parse(raw) as HistoryEntry[];
  } catch {
    return [];
  }
}

function saveHistory(entries: HistoryEntry[]): void {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(entries));
  } catch {
    // localStorage unavailable — ignore
  }
}

export function usePlayHistory() {
  const [history, setHistory] = useState<HistoryEntry[]>(loadHistory);

  const addToHistory = useCallback((track: Track) => {
    setHistory((prev) => {
      // Remove duplicate
      const filtered = prev.filter((e) => e.track.id !== track.id);
      const next: HistoryEntry[] = [
        { track, playedAt: new Date().toISOString() },
        ...filtered,
      ].slice(0, MAX_HISTORY);
      saveHistory(next);
      return next;
    });
  }, []);

  const clearHistory = useCallback(() => {
    setHistory([]);
    try {
      localStorage.removeItem(STORAGE_KEY);
    } catch {
      // ignore
    }
  }, []);

  return { history, addToHistory, clearHistory };
}
