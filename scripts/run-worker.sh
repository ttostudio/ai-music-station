#!/bin/bash
set -euo pipefail

# AI Music Station - Worker runner for host (Apple Silicon)
# Requires: Python 3.11+, PostgreSQL accessible on localhost:5432

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

# Load environment
if [ -f .env ]; then
    set -a
    source .env
    set +a
fi

echo "Starting AI Music Station worker..."
echo "  Database: ${DATABASE_URL:-not set}"
echo "  ACE-Step: ${ACESTEP_API_URL:-http://localhost:8001}"
echo "  Tracks:   ${GENERATED_TRACKS_DIR:-./generated_tracks}"

python3 -m worker
