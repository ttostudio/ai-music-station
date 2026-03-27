export interface NowPlayingInfo {
  track_id: string;
  caption: string;
  started_at: string;
}

export interface Channel {
  id: string;
  slug: string;
  name: string;
  description: string | null;
  is_active: boolean;
  queue_depth: number;
  total_tracks: number;
  stream_url: string;
  now_playing: NowPlayingInfo | null;
}

export interface ChannelDetail extends Channel {
  default_bpm_min: number;
  default_bpm_max: number;
  default_duration: number;
  default_instrumental: boolean;
}

export interface ChannelListResponse {
  channels: Channel[];
}

export interface ChannelCreateBody {
  slug: string;
  name: string;
  description?: string;
  mood_description?: string | null;
  default_bpm_min?: number;
  default_bpm_max?: number;
  default_duration?: number;
  default_key?: string | null;
  default_instrumental?: boolean;
  prompt_template: string;
  vocal_language?: string | null;
  auto_generate?: boolean;
  min_stock?: number;
  max_stock?: number;
}

export interface ChannelFullResponse {
  id: string;
  slug: string;
  name: string;
  description: string | null;
  mood_description: string | null;
  is_active: boolean;
  default_bpm_min: number;
  default_bpm_max: number;
  default_duration: number;
  default_key: string | null;
  default_instrumental: boolean;
  prompt_template: string;
  vocal_language: string | null;
  auto_generate: boolean;
  min_stock: number;
  max_stock: number;
}

export interface ChannelDeleteResponse {
  ok: boolean;
  deleted_tracks: number;
}

export interface CreateRequestBody {
  caption?: string;
  lyrics?: string;
  mood?: string;
  bpm?: number;
  duration?: number;
  music_key?: string;
}

export interface RequestResponse {
  id: string;
  channel_slug: string;
  status: string;
  position: number | null;
  created_at: string;
}

export interface Track {
  id: string;
  caption: string;
  title?: string;
  mood?: string;
  lyrics?: string;
  duration_ms: number | null;
  bpm: number | null;
  music_key: string | null;
  instrumental: boolean | null;
  play_count: number;
  like_count: number;
  quality_score?: number;
  created_at: string;
}

export interface TrackQualityResponse {
  track_id: string;
  score: number;
  auto_drafted: boolean;
  details: {
    duration_sec: number | null;
    bit_rate: number | null;
    sample_rate: number | null;
    mean_volume_db: number | null;
    max_volume_db: number | null;
    silence_ratio: number | null;
    dynamic_range_db: number | null;
    score_breakdown: Record<string, number>;
  };
  scored_at: string;
}

export interface ReactionResponse {
  ok: boolean;
  count: number;
}

export interface ReactionStatusResponse {
  count: number;
  user_reacted: boolean;
}

export interface NowPlayingResponse {
  track: Track | null;
}

export interface TrackListResponse {
  tracks: Track[];
  total: number;
}

export interface ShareLinkResponse {
  share_url: string;
  slug: string;
  track_id: string;
  created_at: string;
}

export interface GenerateRequestBody {
  channel_slug: string;
  mood?: string;
  caption?: string;
  lyrics?: string;
  bpm?: number;
  duration?: number;
  music_key?: string;
}

// --- Playlist types ---

export interface Playlist {
  id: string;
  name: string;
  description: string | null;
  track_count: number;
  created_at: string;
  updated_at: string;
}

export interface PlaylistTrackEntry {
  position: number;
  added_at: string;
  track: Track & { channel_id?: string };
}

export interface PlaylistDetail extends Playlist {
  tracks: PlaylistTrackEntry[];
}

export interface PlaylistListResponse {
  playlists: Playlist[];
  total: number;
  limit: number;
  offset: number;
}

export interface PlaylistCreateBody {
  name: string;
  description?: string;
}

export interface PlaylistUpdateBody {
  name?: string;
  description?: string;
}

export interface PlaylistDeleteResponse {
  ok: boolean;
  deleted_tracks: number;
}

export interface PlaylistAddTrackResponse {
  playlist_id: string;
  track_id: string;
  position: number;
  added_at: string;
}

export interface PlaylistReorderBody {
  track_ids: string[];
}

export interface FavoriteTrack extends Track {
  channel_id: string;
  liked_at: string;
}

export interface FavoritesResponse {
  tracks: FavoriteTrack[];
  total: number;
  limit: number;
  offset: number;
}

// --- End Playlist types ---

export interface RequestDetailResponse {
  id: string;
  channel_slug: string;
  status: "pending" | "processing" | "completed" | "failed";
  mood: string | null;
  caption: string | null;
  lyrics: string | null;
  bpm: number | null;
  duration: number | null;
  music_key: string | null;
  position: number | null;
  created_at: string;
  started_at: string | null;
  completed_at: string | null;
  error_message: string | null;
  track: {
    id: string;
    caption: string;
    duration_ms: number | null;
    bpm: number | null;
    music_key: string | null;
    instrumental: boolean | null;
    play_count: number;
    created_at: string;
  } | null;
}
