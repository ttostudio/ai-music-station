#!/bin/bash
# Called by Liquidsoap on_track to update now-playing metadata
# Args: $1 = channel_slug, $2 = filename (e.g. /tracks/anime/uuid.flac)
CHANNEL="$1"
FILEPATH="$2"
API_BASE_URL="${API_BASE_URL:-http://api:8000}"

# Extract UUID from filename: /tracks/channel/UUID.flac -> UUID
BASENAME=$(basename "$FILEPATH" .flac)
BASENAME=$(basename "$BASENAME" .mp3)
BASENAME=$(basename "$BASENAME" .wav)
BASENAME=$(basename "$BASENAME" .ogg)

# Validate UUID format (8-4-4-4-12)
if echo "$BASENAME" | grep -qE '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'; then
  curl -sf -X POST "${API_BASE_URL}/internal/now-playing" \
    -H "Content-Type: application/json" \
    -d "{\"channel_slug\": \"${CHANNEL}\", \"track_id\": \"${BASENAME}\"}" \
    > /dev/null 2>&1 &
fi
