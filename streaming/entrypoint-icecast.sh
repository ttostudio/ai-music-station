#!/bin/bash
set -e

ICECAST_SOURCE_PASSWORD="${ICECAST_SOURCE_PASSWORD:?required}"
ICECAST_ADMIN_PASSWORD="${ICECAST_ADMIN_PASSWORD:?required}"

# Template the config file (runs as root)
sed -i \
    -e "s|<source-password>changeme</source-password>|<source-password>${ICECAST_SOURCE_PASSWORD}</source-password>|" \
    -e "s|<relay-password>changeme</relay-password>|<relay-password>${ICECAST_SOURCE_PASSWORD}</relay-password>|" \
    -e "s|<admin-password>changeme</admin-password>|<admin-password>${ICECAST_ADMIN_PASSWORD}</admin-password>|" \
    /etc/icecast2/icecast.xml

# Ensure log directory is writable
mkdir -p /var/log/icecast2
chown -R icecast2:icecast /var/log/icecast2 /etc/icecast2

# Drop to icecast2 user
exec gosu icecast2 icecast2 -c /etc/icecast2/icecast.xml
