import { renderHook, act } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { usePlaylistPlayer } from "../hooks/usePlaylistPlayer";
import type { Track } from "../api/types";

vi.mock("../components/AudioVisualizer", () => ({
  resumeAudioContext: vi.fn(),
}));

function makeMockTrack(id: string, title = "Track"): Track {
  return {
    id,
    channel_id: "ch-1",
    title,
    caption: `${title} caption`,
    mood: "chill",
    file_path: `/tracks/${id}.mp3`,
    duration_ms: 180000,
    play_count: 0,
    like_count: 0,
    is_retired: false,
    created_at: new Date().toISOString(),
  } as Track;
}

function createMockAudioRef() {
  const el = {
    src: "",
    currentTime: 0,
    duration: 180,
    load: vi.fn(),
    play: vi.fn().mockResolvedValue(undefined),
    pause: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
  };
  return { current: el as unknown as HTMLAudioElement };
}

describe("usePlaylistPlayer", () => {
  let audioRef: ReturnType<typeof createMockAudioRef>;
  let onSwitchMode: ReturnType<typeof vi.fn>;
  const getAudioUrl = (id: string) => `/api/tracks/${id}/audio`;

  beforeEach(() => {
    audioRef = createMockAudioRef();
    onSwitchMode = vi.fn();
  });

  it("initializes with stream mode", () => {
    const { result } = renderHook(() =>
      usePlaylistPlayer(audioRef, onSwitchMode, getAudioUrl),
    );
    expect(result.current.playMode).toBe("stream");
    expect(result.current.trackQueue).toEqual([]);
    expect(result.current.currentTrackIndex).toBe(0);
    expect(result.current.shuffle).toBe(false);
    expect(result.current.repeat).toBe("off");
    expect(result.current.isTrackPlaying).toBe(false);
  });

  it("playTrack switches to track mode and sets queue", () => {
    const { result } = renderHook(() =>
      usePlaylistPlayer(audioRef, onSwitchMode, getAudioUrl),
    );
    const track = makeMockTrack("t1", "Song 1");

    act(() => {
      result.current.playTrack(track);
    });

    expect(result.current.playMode).toBe("track");
    expect(result.current.trackQueue).toHaveLength(1);
    expect(result.current.currentTrack?.id).toBe("t1");
    expect(onSwitchMode).toHaveBeenCalledWith("track");
  });

  it("playPlaylist sets full queue and starts at given index", () => {
    const { result } = renderHook(() =>
      usePlaylistPlayer(audioRef, onSwitchMode, getAudioUrl),
    );
    const tracks = [
      makeMockTrack("t1", "Song 1"),
      makeMockTrack("t2", "Song 2"),
      makeMockTrack("t3", "Song 3"),
    ];

    act(() => {
      result.current.playPlaylist(tracks, 1);
    });

    expect(result.current.trackQueue).toHaveLength(3);
    expect(result.current.currentTrackIndex).toBe(1);
    expect(result.current.currentTrack?.id).toBe("t2");
  });

  it("playPlaylist does nothing with empty array", () => {
    const { result } = renderHook(() =>
      usePlaylistPlayer(audioRef, onSwitchMode, getAudioUrl),
    );

    act(() => {
      result.current.playPlaylist([]);
    });

    expect(result.current.playMode).toBe("stream");
    expect(result.current.trackQueue).toHaveLength(0);
  });

  it("nextTrack advances index wrapping around", () => {
    const { result } = renderHook(() =>
      usePlaylistPlayer(audioRef, onSwitchMode, getAudioUrl),
    );
    const tracks = [makeMockTrack("t1"), makeMockTrack("t2")];

    act(() => {
      result.current.playPlaylist(tracks, 0);
    });
    act(() => {
      result.current.nextTrack();
    });

    expect(result.current.currentTrackIndex).toBe(1);

    act(() => {
      result.current.nextTrack();
    });

    expect(result.current.currentTrackIndex).toBe(0); // wrap
  });

  it("prevTrack goes back when currentTime <= 3", () => {
    const { result } = renderHook(() =>
      usePlaylistPlayer(audioRef, onSwitchMode, getAudioUrl),
    );
    const tracks = [makeMockTrack("t1"), makeMockTrack("t2")];

    act(() => {
      result.current.playPlaylist(tracks, 1);
    });
    act(() => {
      result.current.prevTrack();
    });

    expect(result.current.currentTrackIndex).toBe(0);
  });

  it("toggleShuffle toggles shuffle state", () => {
    const { result } = renderHook(() =>
      usePlaylistPlayer(audioRef, onSwitchMode, getAudioUrl),
    );

    expect(result.current.shuffle).toBe(false);
    act(() => {
      result.current.toggleShuffle();
    });
    expect(result.current.shuffle).toBe(true);
    act(() => {
      result.current.toggleShuffle();
    });
    expect(result.current.shuffle).toBe(false);
  });

  it("cycleRepeat cycles off → all → one → off", () => {
    const { result } = renderHook(() =>
      usePlaylistPlayer(audioRef, onSwitchMode, getAudioUrl),
    );

    expect(result.current.repeat).toBe("off");
    act(() => {
      result.current.cycleRepeat();
    });
    expect(result.current.repeat).toBe("all");
    act(() => {
      result.current.cycleRepeat();
    });
    expect(result.current.repeat).toBe("one");
    act(() => {
      result.current.cycleRepeat();
    });
    expect(result.current.repeat).toBe("off");
  });

  it("switchToStream pauses audio and switches mode", () => {
    const { result } = renderHook(() =>
      usePlaylistPlayer(audioRef, onSwitchMode, getAudioUrl),
    );

    act(() => {
      result.current.playTrack(makeMockTrack("t1"));
    });
    act(() => {
      result.current.switchToStream();
    });

    expect(result.current.playMode).toBe("stream");
    expect(audioRef.current.pause).toHaveBeenCalled();
    expect(onSwitchMode).toHaveBeenCalledWith("stream");
  });

  it("switchToTrack sets track mode", () => {
    const { result } = renderHook(() =>
      usePlaylistPlayer(audioRef, onSwitchMode, getAudioUrl),
    );

    act(() => {
      result.current.switchToTrack();
    });

    expect(result.current.playMode).toBe("track");
    expect(onSwitchMode).toHaveBeenCalledWith("track");
  });
});
