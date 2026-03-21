#!/bin/bash
set -e

CHANNEL="${CHANNEL:?CHANNEL environment variable is required}"
ICECAST_HOST="${ICECAST_HOST:-icecast}"
ICECAST_PORT="${ICECAST_PORT:-8000}"
ICECAST_SOURCE_PASSWORD="${ICECAST_SOURCE_PASSWORD:?ICECAST_SOURCE_PASSWORD is required}"

# Create track directory if it doesn't exist
mkdir -p "/tracks/${CHANNEL}"

# Touch health file
touch /tmp/liquidsoap_healthy

exec liquidsoap /etc/liquidsoap/channel.liq
