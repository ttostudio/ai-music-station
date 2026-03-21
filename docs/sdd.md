# AI Music Station — Software Design Document

## 1. Overview

AI Music Station is a web application that generates music using ACE-Step v1.5 on Apple Silicon and streams it like a radio station. Users select a channel (LoFi, Anime, Jazz, etc.), optionally request specific songs, and listen to a continuous audio stream in the browser.

## 2. Architecture

```
Browser → Caddy (:3200) → Frontend (React SPA, nginx)
                        → /api/* → FastAPI (:8000)
                        → /stream/* → Icecast2 (:8000)

Icecast2 ← Liquidsoap (1 per channel, reads FLAC from shared volume)
FastAPI ← PostgreSQL (:5432) ← Worker (host-native Python process)
Worker → ACE-Step REST API (:8001, host-native MLX/MPS) → FLAC files → ./generated_tracks/
```

### Services

| Service | Runtime | Port | Description |
|---------|---------|------|-------------|
| postgres | Docker | 5432 | PostgreSQL 16 — queue, metadata, channels |
| api | Docker | 8000 | FastAPI — REST API for channels, requests, tracks |
| icecast | Docker | 8000 | Icecast2 — audio streaming server |
| liquidsoap-{channel} | Docker | — | Liquidsoap — reads tracks, feeds Icecast mount |
| frontend | Docker | 80 | React SPA served by nginx |
| caddy | Docker | 3200 | Reverse proxy (entry point) |
| migrate | Docker | — | Alembic migration runner (run-once) |
| worker | Host | — | ACE-Step queue consumer (Apple Silicon native) |
| ace-step | Host | 8001 | ACE-Step REST API (`uv run acestep-api`) |

## 3. Database Schema

### channels

| Column | Type | Description |
|--------|------|-------------|
| id | UUID PK | |
| slug | VARCHAR(50) UNIQUE | URL-safe identifier (e.g., "lofi") |
| name | VARCHAR(100) | Display name (e.g., "LoFi Beats") |
| description | TEXT | Channel description |
| is_active | BOOLEAN | Whether channel accepts requests |
| default_bpm_min | INTEGER | Min BPM for generation |
| default_bpm_max | INTEGER | Max BPM for generation |
| default_duration | INTEGER | Default track duration (seconds) |
| default_key | VARCHAR(10) | Default musical key |
| default_instrumental | BOOLEAN | Default instrumental flag |
| prompt_template | TEXT | Base caption template for ACE-Step |
| vocal_language | VARCHAR(10) | Language code (e.g., "ja", "en") |
| created_at | TIMESTAMPTZ | |
| updated_at | TIMESTAMPTZ | |

### requests

| Column | Type | Description |
|--------|------|-------------|
| id | UUID PK | |
| channel_id | UUID FK→channels | |
| status | VARCHAR(20) | pending → processing → completed / failed |
| caption | TEXT | User-provided description |
| lyrics | TEXT | User-provided lyrics |
| bpm | INTEGER | Requested BPM override |
| duration | INTEGER | Requested duration override (seconds) |
| music_key | VARCHAR(10) | Requested key override |
| worker_id | VARCHAR(100) | Hostname of claiming worker |
| started_at | TIMESTAMPTZ | When processing began |
| completed_at | TIMESTAMPTZ | When processing finished |
| error_message | TEXT | Error details if failed |
| created_at | TIMESTAMPTZ | |
| updated_at | TIMESTAMPTZ | |

### tracks

| Column | Type | Description |
|--------|------|-------------|
| id | UUID PK | |
| request_id | UUID FK→requests (UNIQUE) | |
| channel_id | UUID FK→channels | |
| file_path | VARCHAR(500) | Relative path in generated_tracks/ |
| file_size | BIGINT | File size in bytes |
| duration_ms | INTEGER | Actual audio duration |
| sample_rate | INTEGER | Sample rate (default 48000) |
| caption | TEXT | Actual caption sent to ACE-Step |
| lyrics | TEXT | Actual lyrics sent |
| bpm | INTEGER | Actual BPM used |
| music_key | VARCHAR(10) | Actual key used |
| instrumental | BOOLEAN | Whether instrumental |
| num_steps | INTEGER | Denoising steps used |
| cfg_scale | FLOAT | CFG scale used |
| seed | BIGINT | Random seed used |
| play_count | INTEGER | Times played on stream |
| last_played_at | TIMESTAMPTZ | |
| created_at | TIMESTAMPTZ | |

### now_playing

| Column | Type | Description |
|--------|------|-------------|
| channel_id | UUID PK FK→channels | |
| track_id | UUID FK→tracks | |
| started_at | TIMESTAMPTZ | When track started playing |

### Indexes

- `idx_requests_pending` — `(status, created_at) WHERE status = 'pending'`
- `idx_requests_channel` — `(channel_id, status)`
- `idx_tracks_channel` — `(channel_id, created_at DESC)`

## 4. API Contract

Base URL: `/api`

### Health

```
GET /api/health → 200
{
  "status": "healthy",
  "database": "connected",
  "worker_last_seen": "ISO8601" | null,
  "channels_active": 3
}
```

### Channels

```
GET /api/channels → 200
{
  "channels": [{
    "id": "uuid", "slug": "lofi", "name": "LoFi Beats",
    "description": "...", "is_active": true,
    "queue_depth": 3, "total_tracks": 42,
    "stream_url": "/stream/lofi.ogg",
    "now_playing": { "track_id": "uuid", "caption": "...", "started_at": "ISO8601" } | null
  }]
}

GET /api/channels/{slug} → 200 | 404
  Same as above + default_bpm_min, default_bpm_max, default_duration, default_instrumental
```

### Requests

```
POST /api/channels/{slug}/requests → 201 | 404 | 422
Body: { "caption"?: string, "lyrics"?: string, "bpm"?: int, "duration"?: int, "music_key"?: string }
Response: { "id": "uuid", "channel_slug": "lofi", "status": "pending", "position": 4, "created_at": "ISO8601" }

GET /api/channels/{slug}/requests?status=pending&limit=20&offset=0 → 200
{ "requests": [...], "total": 15 }

GET /api/requests/{id} → 200 | 404
{ "id", "channel_slug", "status", "caption", "position", "created_at", "started_at", "completed_at", "track": {...} | null }
```

### Tracks

```
GET /api/channels/{slug}/tracks?limit=20&offset=0 → 200
{ "tracks": [{ "id", "caption", "duration_ms", "bpm", "music_key", "instrumental", "play_count", "created_at" }], "total": 42 }

GET /api/channels/{slug}/now-playing → 200
{ "track": { "id", "caption", "duration_ms", "elapsed_ms", "bpm", "music_key" } | null }
```

### Internal (not exposed via Caddy)

```
POST /internal/now-playing
Body: { "channel_slug": "lofi", "track_id": "uuid" } → 200

POST /internal/worker-heartbeat
Body: { "worker_id": "macmini-1", "active_request_id": "uuid" | null } → 200
```

## 5. Streaming Architecture

### Icecast2

Mount points per channel:
- `/lofi.ogg` — OGG Vorbis
- `/anime.ogg` — OGG Vorbis
- `/jazz.ogg` — OGG Vorbis

### Liquidsoap

One container per channel. Each:
1. Watches `generated_tracks/{channel_slug}/` for FLAC files
2. Maintains a playlist with automatic reload
3. Crossfades between tracks (3-second fade)
4. Falls back to silence when no tracks exist
5. Encodes to OGG Vorbis and pushes to Icecast mount point
6. Calls `/internal/now-playing` on track change

### Browser Playback

HTML5 `<audio>` element pointed at Icecast stream URL via Caddy:
```
<audio src="/stream/lofi.ogg" />
```

## 6. ACE-Step Worker

Runs natively on Mac mini (not Docker) for MPS/MLX access.

### Connection

- PostgreSQL: `localhost:5432` (exposed by Docker)
- ACE-Step API: `localhost:8001` (host-native `uv run acestep-api`)
- Output: `./generated_tracks/{channel_slug}/{track_id}.flac` (bind mount)

### Queue Processing Loop

```
every 2 seconds:
  SELECT * FROM requests WHERE status='pending'
    ORDER BY created_at
    FOR UPDATE SKIP LOCKED LIMIT 1

  if found:
    UPDATE status='processing', worker_id=hostname, started_at=now()
    build params from request + channel presets
    POST http://localhost:8001/generate → FLAC
    save to generated_tracks/{channel}/{id}.flac
    INSERT INTO tracks
    UPDATE request status='completed'

  on error:
    UPDATE request status='failed', error_message=str(error)
```

### Channel Presets

| Channel | BPM | Key | Instrumental | Language | Prompt Template |
|---------|-----|-----|-------------|----------|-----------------|
| LoFi | 70-90 | minor | true | — | "lo-fi hip hop beat, chill, relaxed, vinyl crackle, mellow piano, ambient" |
| Anime | 120-160 | major | false | ja | "anime opening theme, energetic, J-pop, catchy melody, orchestral" |
| Jazz | 100-140 | various | true | — | "jazz, smooth, saxophone, piano, upright bass, drums, improvisational" |

## 7. Docker Compose

Project name: `product-ai-music-station`

Services: postgres, migrate, api, icecast, liquidsoap-lofi, liquidsoap-anime, liquidsoap-jazz, frontend, caddy

All services have health checks. Secrets via `.env` file.

### Caddy Routing

```
:3200 {
    handle /api/* {
        reverse_proxy api:8000
    }
    handle /stream/* {
        uri strip_prefix /stream
        reverse_proxy icecast:8000
    }
    handle {
        reverse_proxy frontend:80
    }
}
```

## 8. Default Channels

| Slug | Name | Description |
|------|------|-------------|
| lofi | LoFi Beats | Chill lo-fi hip hop beats to relax and study to |
| anime | Anime Songs | AI-generated anime opening and ending themes |
| jazz | Jazz Station | Smooth jazz, improvisation, and classic vibes |
