import type {
  ChannelCreateBody,
  ChannelDeleteResponse,
  ChannelFullResponse,
  ChannelListResponse,
  CreateRequestBody,
  GenerateRequestBody,
  NowPlayingResponse,
  ReactionResponse,
  ReactionStatusResponse,
  RequestDetailResponse,
  RequestResponse,
  ShareLinkResponse,
  TrackListResponse,
  TrackQualityResponse,
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

export async function addReaction(
  trackId: string,
  sessionId: string,
): Promise<ReactionResponse> {
  return fetchJSON<ReactionResponse>(
    `${BASE_URL}/tracks/${trackId}/reactions`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ session_id: sessionId, reaction_type: "like" }),
    },
  );
}

export async function removeReaction(
  trackId: string,
  sessionId: string,
): Promise<ReactionResponse> {
  return fetchJSON<ReactionResponse>(
    `${BASE_URL}/tracks/${trackId}/reactions`,
    {
      method: "DELETE",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ session_id: sessionId }),
    },
  );
}

export async function getReaction(
  trackId: string,
  sessionId: string,
): Promise<ReactionStatusResponse> {
  return fetchJSON<ReactionStatusResponse>(
    `${BASE_URL}/tracks/${trackId}/reactions?session_id=${encodeURIComponent(sessionId)}`,
  );
}

export async function createChannel(
  body: ChannelCreateBody,
): Promise<ChannelFullResponse> {
  return fetchJSON<ChannelFullResponse>(`${BASE_URL}/channels`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}

export async function updateChannel(
  slug: string,
  body: ChannelCreateBody,
): Promise<ChannelFullResponse> {
  return fetchJSON<ChannelFullResponse>(`${BASE_URL}/channels/${slug}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}

export async function deleteChannel(
  slug: string,
): Promise<ChannelDeleteResponse> {
  return fetchJSON<ChannelDeleteResponse>(`${BASE_URL}/channels/${slug}`, {
    method: "DELETE",
  });
}

export async function createShareLink(
  trackId: string,
): Promise<ShareLinkResponse> {
  return fetchJSON<ShareLinkResponse>(`${BASE_URL}/tracks/${trackId}/share`, {
    method: "POST",
  });
}

export async function getTrackQuality(
  trackId: string,
): Promise<TrackQualityResponse> {
  return fetchJSON<TrackQualityResponse>(
    `${BASE_URL}/tracks/${trackId}/quality`,
  );
}

export async function submitGenerate(
  body: GenerateRequestBody,
): Promise<RequestResponse> {
  return fetchJSON<RequestResponse>(`${BASE_URL}/generate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}

export async function getGenerateStatus(
  requestId: string,
): Promise<RequestDetailResponse> {
  return fetchJSON<RequestDetailResponse>(
    `${BASE_URL}/generate/${requestId}/status`,
  );
}
