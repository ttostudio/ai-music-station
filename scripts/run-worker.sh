#!/bin/bash
set -euo pipefail

# AI Music Station - ワーカー実行スクリプト (Apple Silicon)
# 前提条件: setup-worker.sh でセットアップ済み

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

# 仮想環境の有効化
if [ -f .venv/bin/activate ]; then
    source .venv/bin/activate
else
    echo "エラー: .venv が見つかりません。先に ./scripts/setup-worker.sh を実行してください。"
    exit 1
fi

# 環境変数の読み込み
if [ -f .env ]; then
    set -a
    source .env
    set +a
fi

echo "AI Music Station ワーカーを起動中..."
echo "  データベース: ${DATABASE_URL:-未設定}"
echo "  ACE-Step: ${ACESTEP_API_URL:-http://localhost:8001}"
echo "  トラック: ${GENERATED_TRACKS_DIR:-./generated_tracks}"

python -m worker
