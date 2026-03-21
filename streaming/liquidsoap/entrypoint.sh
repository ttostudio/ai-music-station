#!/bin/bash
set -e

CHANNEL="${CHANNEL:?CHANNEL environment variable is required}"
ICECAST_HOST="${ICECAST_HOST:-icecast}"
ICECAST_PORT="${ICECAST_PORT:-8000}"
ICECAST_SOURCE_PASSWORD="${ICECAST_SOURCE_PASSWORD:?ICECAST_SOURCE_PASSWORD is required}"

# Create track directory if it doesn't exist
mkdir -p "/tracks/${CHANNEL}"

# playlist.m3u がなければ空ファイルを作成（liquidsoap 起動時エラー防止）
PLAYLIST_FILE="/tracks/${CHANNEL}/playlist.m3u"
if [ ! -f "${PLAYLIST_FILE}" ]; then
    touch "${PLAYLIST_FILE}"
fi

# Touch health file
touch /tmp/liquidsoap_healthy

exec liquidsoap /etc/liquidsoap/channel.liq
