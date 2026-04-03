#!/bin/bash
# ACE-Step スケジュール起動スクリプト
# cron: 0 2 * * * /Users/tto/.ttoClaw/workspace/products/ai-music-station/scripts/schedule-acestep.sh >> ~/logs/acestep/cron.log 2>&1

set -euo pipefail

LOCK_FILE="/tmp/acestep-schedule.lock"
LOG_DIR="$HOME/logs/acestep"
LOG_FILE="$LOG_DIR/schedule-$(date +%Y%m%d).log"
MUSIC_DIR="/Users/tto/.ttoClaw/workspace/products/ai-music-station"
ACESTEP_DIR="$HOME/ACE-Step"
COMFYUI_CONTAINER="comfyui-comfyui-1"

mkdir -p "$LOG_DIR"

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG_FILE"; }

# ロック管理
if [ -f "$LOCK_FILE" ]; then
    PID=$(cat "$LOCK_FILE")
    if kill -0 "$PID" 2>/dev/null; then
        log "既に実行中 (PID: $PID)"
        exit 1
    fi
    rm -f "$LOCK_FILE"
fi
echo $$ > "$LOCK_FILE"
trap "rm -f $LOCK_FILE" EXIT

# GPU メモリ確認（Apple Silicon / NVIDIA 両対応）
check_gpu() {
    if command -v nvidia-smi &> /dev/null; then
        # NVIDIA GPU
        FREE_VRAM=$(nvidia-smi --query-gpu=memory.free --format=csv,noheader,nounits | head -1)
        if [ "$FREE_VRAM" -lt 8000 ]; then
            log "✗ VRAM 空き不足: ${FREE_VRAM}MB（要8GB以上）"
            return 1
        fi
        log "GPU VRAM 空き: ${FREE_VRAM}MB"
    else
        # Apple Silicon — 統合メモリのため VRAM 専用チェック不可
        log "Apple Silicon 検出: GPU メモリチェックをスキップ"
    fi
    return 0
}

# 1. ComfyUI 停止（GPU共有）
log "ComfyUI 停止中..."
docker stop "$COMFYUI_CONTAINER" 2>/dev/null || log "ComfyUI は既に停止"

# 1.5. GPU メモリ確認
if ! check_gpu; then
    log "GPU メモリ不足のため中断。ComfyUI を再起動します"
    docker start "$COMFYUI_CONTAINER" 2>/dev/null || true
    exit 1
fi

# 2. ACE-Step 起動
log "ACE-Step 起動中..."
cd "$ACESTEP_DIR"
python3 acestep_server.py --port 8001 &
ACESTEP_PID=$!
sleep 30  # モデルロード待ち

# 3. ACE-Step ヘルスチェック
if ! curl -s http://localhost:8001/v1/models > /dev/null; then
    log "✗ ACE-Step 起動失敗"
    kill "$ACESTEP_PID" 2>/dev/null
    docker start "$COMFYUI_CONTAINER" 2>/dev/null
    exit 1
fi
log "ACE-Step 起動OK"

# 4. 在庫補充
log "楽曲生成開始..."
cd "$MUSIC_DIR"
python3 scripts/generate-being-tracks.py --channel being --music-api-url http://localhost:3600/api 2>&1 | tee -a "$LOG_FILE"

# 5. ACE-Step 停止
log "ACE-Step 停止中..."
kill "$ACESTEP_PID" 2>/dev/null
wait "$ACESTEP_PID" 2>/dev/null || true

# 6. ComfyUI 再起動
log "ComfyUI 再起動中..."
docker start "$COMFYUI_CONTAINER" 2>/dev/null || log "ComfyUI 起動失敗"

log "スケジュール完了"
