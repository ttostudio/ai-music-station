# AI Music Station

ACE-Step v1.5 powered music generation and streaming service. Request songs by channel (anime, LoFi, etc.) and listen via browser like a radio station.

## Overview

AI Music Station runs ACE-Step v1.5 on Mac mini (Apple Silicon) to generate music on-demand, queue tracks, and stream them like a radio station. Accessible via Tailscale.

## Features

- Per-channel music requests (e.g., anime song channel, LoFi channel, jazz channel)
- Music generation using ACE-Step v1.5 on Apple Silicon
- Queue management with automatic playback
- Browser-based streaming player (HLS/Icecast)
- Self-contained Docker Compose deployment
- Start/Stop from AI Company OS dashboard

## Tech Stack

- **Music Generation:** ACE-Step v1.5 (Apple Silicon optimized)
- **Backend:** Python (FastAPI - generation queue & API)
- **Streaming:** Icecast / HLS
- **Frontend:** React (player UI with channel selector)
- **Database:** PostgreSQL (track metadata, queue, channels)
- **Infrastructure:** Docker Compose, Caddy (reverse proxy)

## Getting Started

### Prerequisites

- Docker & Docker Compose
- Mac mini with Apple Silicon (for ACE-Step inference)
- Python 3.11+ (for music generation worker)

### Quick Start

```bash
cp .env.example .env
# Edit .env with your configuration
docker compose up -d
```

The music station will be available at `http://localhost:3200`.

## Development

```bash
# Install dependencies
pip install -r requirements.txt
npm install

# Run tests
pytest
npm test

# Run linter
ruff check .
npm run lint
```

## Architecture

```
Channel Request (web UI / API)
  -> Request Queue (PostgreSQL)
  -> ACE-Step v1.5 Worker (music generation)
  -> Generated Track Storage
  -> Streaming Server (Icecast/HLS)
  -> Web Player (browser)
```

## License

MIT - see [LICENSE](LICENSE) for details.

## Contributing

This is an open source project by [ttoStudio](https://github.com/ttostudio). Contributions are welcome!
