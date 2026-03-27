import type {
  FavoritesResponse,
  PlaylistAddTrackResponse,
  PlaylistCreateBody,
  PlaylistDeleteResponse,
  PlaylistDetail,
  PlaylistListResponse,
  PlaylistReorderBody,
  PlaylistUpdateBody,
} from "./types";

const BASE_URL = "/api";

export function getSessionId(): string {
  let id = localStorage.getItem("session-id");
  if (!id) {
    id = crypto.randomUUID();
    localStorage.setItem("session-id", id);
  }
  return id;
}

async function fetchJSON<T>(url: string, init?: RequestInit): Promise<T> {
  const sessionId = getSessionId();
  const response = await fetch(url, {
    ...init,
    headers: {
      "X-Session-ID": sessionId,
      ...(init?.body ? { "Content-Type": "application/json" } : {}),
      ...init?.headers,
    },
  });
  if (!response.ok) {
    throw new Error(`API error: ${response.status} ${response.statusText}`);
  }
  return response.json() as Promise<T>;
}

export async function getPlaylists(
  limit = 50,
  offset = 0,
): Promise<PlaylistListResponse> {
  return fetchJSON<PlaylistListResponse>(
    `${BASE_URL}/playlists?limit=${limit}&offset=${offset}`,
  );
}

export async function getPlaylist(playlistId: string): Promise<PlaylistDetail> {
  return fetchJSON<PlaylistDetail>(`${BASE_URL}/playlists/${playlistId}`);
}

export async function createPlaylist(
  body: PlaylistCreateBody,
): Promise<PlaylistDetail> {
  return fetchJSON<PlaylistDetail>(`${BASE_URL}/playlists`, {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export async function updatePlaylist(
  playlistId: string,
  body: PlaylistUpdateBody,
): Promise<PlaylistDetail> {
  return fetchJSON<PlaylistDetail>(`${BASE_URL}/playlists/${playlistId}`, {
    method: "PATCH",
    body: JSON.stringify(body),
  });
}

export async function deletePlaylist(
  playlistId: string,
): Promise<PlaylistDeleteResponse> {
  return fetchJSON<PlaylistDeleteResponse>(
    `${BASE_URL}/playlists/${playlistId}`,
    { method: "DELETE" },
  );
}

export async function addTrackToPlaylist(
  playlistId: string,
  trackId: string,
): Promise<PlaylistAddTrackResponse> {
  return fetchJSON<PlaylistAddTrackResponse>(
    `${BASE_URL}/playlists/${playlistId}/tracks`,
    {
      method: "POST",
      body: JSON.stringify({ track_id: trackId }),
    },
  );
}

export async function removeTrackFromPlaylist(
  playlistId: string,
  trackId: string,
): Promise<{ ok: boolean }> {
  return fetchJSON<{ ok: boolean }>(
    `${BASE_URL}/playlists/${playlistId}/tracks/${trackId}`,
    { method: "DELETE" },
  );
}

export async function reorderPlaylistTracks(
  playlistId: string,
  body: PlaylistReorderBody,
): Promise<{ ok: boolean }> {
  return fetchJSON<{ ok: boolean }>(
    `${BASE_URL}/playlists/${playlistId}/tracks/reorder`,
    {
      method: "PUT",
      body: JSON.stringify(body),
    },
  );
}

export async function getFavorites(
  limit = 50,
  offset = 0,
): Promise<FavoritesResponse> {
  return fetchJSON<FavoritesResponse>(
    `${BASE_URL}/favorites?limit=${limit}&offset=${offset}`,
  );
}
