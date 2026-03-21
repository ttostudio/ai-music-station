# AI Music Station

ACE-Step v1.5 powered music generation and streaming service. Request songs by channel (anime, LoFi, jazz) and listen via browser like a radio station.

## Architecture

```
Browser → Caddy (:3200) → Frontend (React SPA)
                        → /api/* → FastAPI (:8000)
                        → /stream/* → Icecast2 (:8000)

Icecast2 ← Liquidsoap (1 per channel, reads FLAC from shared volume)
FastAPI ← PostgreSQL (:5432) ← Worker (host-native Python process)
Worker → ACE-Step API (:8001, host-native MLX) → FLAC → ./generated_tracks/
```

### Services

| Service | Runtime | Description |
|---------|---------|-------------|
| `postgres` | Docker | PostgreSQL 16 — queue, metadata, channels |
| `api` | Docker | FastAPI — REST API |
| `icecast` | Docker | Icecast2 — audio streaming |
| `liquidsoap-{lofi,anime,jazz}` | Docker | Liquidsoap — reads tracks, feeds Icecast |
| `frontend` | Docker | React SPA (nginx) |
| `caddy` | Docker | Reverse proxy (port 3200) |
| `worker` | Host | ACE-Step queue consumer (Apple Silicon) |

## Quick Start

### 1. Clone and configure

```bash
git clone https://github.com/ttostudio/ai-music-station.git
cd ai-music-station
cp .env.example .env
# Edit .env with secure passwords
```

### 2. Start Docker services

```bash
docker compose up -d
```

This starts PostgreSQL, runs migrations, seeds channels, starts the API, Icecast2 streaming, Liquidsoap per channel, frontend, and Caddy reverse proxy.

### 3. Set up the worker (Apple Silicon host)

The music generation worker runs on the host Mac mini for MPS/MLX GPU access:

```bash
# Run the setup script
./scripts/setup-worker.sh

# Start ACE-Step API (in a separate terminal)
cd ~/ace-step && uv run acestep-api

# Start the worker
python3 -m worker
```

### 4. Open the player

Visit **http://localhost:3200** in your browser.

## Channels

| Channel | Style | BPM | Duration |
|---------|-------|-----|----------|
| LoFi Beats | Chill lo-fi hip hop | 70-90 | 180s |
| Anime Songs | J-pop anime themes | 120-160 | 90s |
| Jazz Station | Smooth jazz | 100-140 | 240s |

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health` | Health check |
| GET | `/api/channels` | List channels |
| GET | `/api/channels/{slug}` | Channel detail |
| POST | `/api/channels/{slug}/requests` | Submit song request |
| GET | `/api/channels/{slug}/tracks` | List generated tracks |
| GET | `/api/channels/{slug}/now-playing` | Current track |

## Development

```bash
# Python
pip install -r requirements.txt
ruff check .
pytest

# Frontend
cd frontend && npm ci
npm run lint
npm test

# Docker
docker compose config  # validate
```

## Tech Stack

- **Music Generation:** ACE-Step v1.5 (Apple Silicon MLX)
- **Backend:** Python FastAPI + SQLAlchemy + Alembic
- **Streaming:** Icecast2 + Liquidsoap (OGG Vorbis)
- **Frontend:** React 19 + Vite + Tailwind CSS
- **Database:** PostgreSQL 16
- **Infrastructure:** Docker Compose, Caddy

## License

MIT — see [LICENSE](LICENSE) for details.
