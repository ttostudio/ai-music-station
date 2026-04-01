import { renderHook, act } from "@testing-library/react";
import { describe, it, expect, beforeEach, afterEach, vi } from "vitest";
import { usePlayHistory } from "../hooks/usePlayHistory";
import type { Track } from "../api/types";

const storageMock = (() => {
  let store: Record<string, string> = {};
  return {
    getItem: (key: string) => store[key] ?? null,
    setItem: (key: string, value: string) => { store[key] = value; },
    removeItem: (key: string) => { delete store[key]; },
    clear: () => { store = {}; },
  };
})();

const makeTrack = (id: string, title: string): Track => ({
  id,
  title,
  caption: `Caption for ${title}`,
  mood: "chill",
  duration_ms: 180000,
  bpm: 120,
  music_key: "Am",
  instrumental: true,
  play_count: 0,
  like_count: 0,
  created_at: "2026-04-01T00:00:00Z",
});

describe("usePlayHistory", () => {
  beforeEach(() => {
    vi.stubGlobal("localStorage", storageMock);
    storageMock.clear();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("初期状態は空のリスト", () => {
    const { result } = renderHook(() => usePlayHistory());
    expect(result.current.history).toHaveLength(0);
  });

  it("トラックを追加できる", () => {
    const { result } = renderHook(() => usePlayHistory());
    const track = makeTrack("t1", "Track 1");

    act(() => {
      result.current.addToHistory(track);
    });

    expect(result.current.history).toHaveLength(1);
    expect(result.current.history[0].track.id).toBe("t1");
  });

  it("新しいトラックが先頭に来る", () => {
    const { result } = renderHook(() => usePlayHistory());
    act(() => {
      result.current.addToHistory(makeTrack("t1", "Track 1"));
    });
    act(() => {
      result.current.addToHistory(makeTrack("t2", "Track 2"));
    });

    expect(result.current.history[0].track.id).toBe("t2");
    expect(result.current.history[1].track.id).toBe("t1");
  });

  it("重複トラックは先頭に移動される", () => {
    const { result } = renderHook(() => usePlayHistory());
    act(() => {
      result.current.addToHistory(makeTrack("t1", "Track 1"));
    });
    act(() => {
      result.current.addToHistory(makeTrack("t2", "Track 2"));
    });
    act(() => {
      result.current.addToHistory(makeTrack("t1", "Track 1"));
    });

    expect(result.current.history).toHaveLength(2);
    expect(result.current.history[0].track.id).toBe("t1");
  });

  it("最大20件までに制限される", () => {
    const { result } = renderHook(() => usePlayHistory());
    act(() => {
      for (let i = 0; i < 25; i++) {
        result.current.addToHistory(makeTrack(`t${i}`, `Track ${i}`));
      }
    });

    expect(result.current.history).toHaveLength(20);
  });

  it("clearHistory で履歴が空になる", () => {
    const { result } = renderHook(() => usePlayHistory());
    act(() => {
      result.current.addToHistory(makeTrack("t1", "Track 1"));
    });
    expect(result.current.history).toHaveLength(1);

    act(() => {
      result.current.clearHistory();
    });
    expect(result.current.history).toHaveLength(0);
  });

  it("localStorage に永続化される", () => {
    const { result } = renderHook(() => usePlayHistory());
    act(() => {
      result.current.addToHistory(makeTrack("t1", "Track 1"));
    });

    const stored = localStorage.getItem("ai-music-station:history");
    expect(stored).not.toBeNull();
    const parsed = JSON.parse(stored!);
    expect(parsed[0].track.id).toBe("t1");
  });
});
