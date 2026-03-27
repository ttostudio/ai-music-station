import { describe, it, expect, vi, afterEach, beforeEach } from "vitest";
import {
  getSessionId,
  getPlaylists,
  createPlaylist,
  deletePlaylist,
} from "../api/playlists";

// Mock localStorage to avoid --localstorage-file interference
const storageMock = (() => {
  let store: Record<string, string> = {};
  return {
    getItem: (key: string) => store[key] ?? null,
    setItem: (key: string, value: string) => {
      store[key] = value;
    },
    removeItem: (key: string) => {
      delete store[key];
    },
    clear: () => {
      store = {};
    },
  };
})();

beforeEach(() => {
  vi.stubGlobal("localStorage", storageMock);
});

afterEach(() => {
  storageMock.clear();
  vi.restoreAllMocks();
});

describe("getSessionId", () => {
  it("UT-SID-01: 初回は UUID を生成して localStorage に保存する", () => {
    const id = getSessionId();
    expect(id).toMatch(
      /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i,
    );
    expect(localStorage.getItem("session-id")).toBe(id);
  });

  it("UT-SID-02: 2回目以降は同じ ID を返す", () => {
    const id1 = getSessionId();
    const id2 = getSessionId();
    expect(id1).toBe(id2);
  });
});

describe("Playlists API", () => {
  beforeEach(() => {
    localStorage.setItem("session-id", "test-session-uuid");
  });

  it("UT-API-01: getPlaylists は GET /api/playlists を呼ぶ", async () => {
    const mockResponse = {
      playlists: [],
      total: 0,
      limit: 50,
      offset: 0,
    };
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: () => Promise.resolve(mockResponse),
      }),
    );

    const result = await getPlaylists();
    expect(result).toEqual(mockResponse);

    const fetchMock = vi.mocked(fetch);
    expect(fetchMock).toHaveBeenCalledOnce();
    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toBe("/api/playlists?limit=50&offset=0");
    expect((init as RequestInit).headers).toMatchObject({
      "X-Session-ID": "test-session-uuid",
    });
  });

  it("UT-API-02: createPlaylist は POST /api/playlists を呼ぶ", async () => {
    const mockPlaylist = {
      id: "uuid",
      name: "テスト",
      description: null,
      track_count: 0,
      tracks: [],
      created_at: "2026-03-27T00:00:00Z",
      updated_at: "2026-03-27T00:00:00Z",
    };
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: () => Promise.resolve(mockPlaylist),
      }),
    );

    const result = await createPlaylist({ name: "テスト" });
    expect(result.name).toBe("テスト");

    const fetchMock = vi.mocked(fetch);
    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toBe("/api/playlists");
    expect((init as RequestInit).method).toBe("POST");
  });

  it("UT-API-03: deletePlaylist は DELETE /api/playlists/:id を呼ぶ", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({ ok: true, deleted_tracks: 3 }),
      }),
    );

    const result = await deletePlaylist("uuid-1");
    expect(result.ok).toBe(true);

    const fetchMock = vi.mocked(fetch);
    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toBe("/api/playlists/uuid-1");
    expect((init as RequestInit).method).toBe("DELETE");
  });

  it("UT-API-04: API エラー時は Error をスローする", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: false,
        status: 404,
        statusText: "Not Found",
      }),
    );

    await expect(getPlaylists()).rejects.toThrow("API error: 404 Not Found");
  });
});
