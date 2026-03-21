import type {
  ChannelListResponse,
  CreateRequestBody,
  NowPlayingResponse,
  RequestResponse,
  TrackListResponse,
} from "./types";

const BASE_URL = "/api";

async function fetchJSON<T>(url: string, init?: RequestInit): Promise<T> {
  const response = await fetch(url, init);
  if (!response.ok) {
    throw new Error(`API error: ${response.status} ${response.statusText}`);
  }
  return response.json() as Promise<T>;
}

export async function getChannels(): Promise<ChannelListResponse> {
  return fetchJSON<ChannelListResponse>(`${BASE_URL}/channels`);
}

export async function getNowPlaying(
  slug: string,
): Promise<NowPlayingResponse> {
  return fetchJSON<NowPlayingResponse>(
    `${BASE_URL}/channels/${slug}/now-playing`,
  );
}

export async function getTracks(
  slug: string,
  limit = 20,
): Promise<TrackListResponse> {
  return fetchJSON<TrackListResponse>(
    `${BASE_URL}/channels/${slug}/tracks?limit=${limit}`,
  );
}

export async function createRequest(
  slug: string,
  body: CreateRequestBody,
): Promise<RequestResponse> {
  return fetchJSON<RequestResponse>(`${BASE_URL}/channels/${slug}/requests`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}
