#!/bin/bash
set -e

# AI Music Station — 統合Liquidsoapエントリポイント
# APIからアクティブチャンネル一覧を取得し、動的にLiquidsoap設定を生成する

ICECAST_HOST="${ICECAST_HOST:-icecast}"
ICECAST_PORT="${ICECAST_PORT:-8000}"
ICECAST_SOURCE_PASSWORD="${ICECAST_SOURCE_PASSWORD:?ICECAST_SOURCE_PASSWORD is required}"
API_BASE_URL="${API_BASE_URL:-http://api:8000}"

# APIからアクティブチャンネル一覧を取得
echo "チャンネル一覧を取得中: ${API_BASE_URL}/api/channels"
CHANNELS=$(curl -sf "${API_BASE_URL}/api/channels" | python3 -c "
import json, sys
data = json.load(sys.stdin)
channels = data.get('channels', [])
for ch in channels:
    if ch.get('is_active', True):
        print(ch['slug'])
")

if [ -z "$CHANNELS" ]; then
    echo "警告: アクティブなチャンネルがありません。silence のみで起動します。"
fi

# 各チャンネルのディレクトリと playlist.m3u を作成
for ch in $CHANNELS; do
    mkdir -p "/tracks/${ch}"
    [ -f "/tracks/${ch}/playlist.m3u" ] || touch "/tracks/${ch}/playlist.m3u"
    echo "チャンネル準備完了: ${ch}"
done

# Liquidsoap設定を動的生成
cat > /tmp/radio.liq << LIQEOF
# AI Music Station — 統合ラジオ設定（全チャンネル）
silence_file = "/etc/liquidsoap/silence.wav"
silence = single(silence_file)

icecast_host = "${ICECAST_HOST}"
icecast_port = ${ICECAST_PORT}
icecast_password = "${ICECAST_SOURCE_PASSWORD}"
LIQEOF

# 各チャンネルの設定を追加
for ch in $CHANNELS; do
    # Liquidsoap変数名にハイフンは使えないのでアンダースコアに変換
    var=$(echo "$ch" | tr '-' '_')
    cat >> /tmp/radio.liq << LIQEOF

# --- Channel: ${ch} ---
${var}_playlist = playlist(mode="normal", reload_mode="watch", "/tracks/${ch}/playlist.m3u")
${var}_dir = playlist(mode="randomize", reload_mode="watch", "/tracks/${ch}")
${var}_radio = playlist(mode="randomize", reload=10, "/tracks/${ch}/playlist.m3u")
${var}_radio = fallback(track_sensitive=false, [${var}_radio, silence])

output.icecast(
  %vorbis(quality=0.5),
  host=icecast_host,
  port=icecast_port,
  password=icecast_password,
  mount="/${ch}.ogg",
  name="AI Music Station - ${ch}",
  description="AI-generated music stream",
  ${var}_radio
)
LIQEOF
    echo "Liquidsoap設定追加: ${ch} (変数名: ${var})"
done

echo "Liquidsoap設定生成完了。起動します。"
touch /tmp/liquidsoap_healthy
exec liquidsoap /tmp/radio.liq
