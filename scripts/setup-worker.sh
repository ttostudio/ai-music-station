#!/bin/bash
set -euo pipefail

# AI Music Station - Apple Silicon ホスト用ワーカーセットアップ
# MPS/MLX GPU アクセスのため、Docker 外で実行

echo "=== AI Music Station ワーカーセットアップ ==="

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
ACESTEP_DIR="${HOME}/ace-step"

cd "$PROJECT_DIR"

# 1. uv の確認・インストール
if ! command -v uv &> /dev/null; then
    echo "uv パッケージマネージャーをインストール中..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$PATH"
fi
echo "  uv: $(uv --version)"

# 2. Python 3.12 の仮想環境を作成
echo "Python 3.12 仮想環境を作成中..."
uv venv --python 3.12 .venv
source .venv/bin/activate
echo "  Python: $(python --version)"

# 3. ワーカー依存パッケージのインストール
echo "ワーカー依存パッケージをインストール中..."
uv pip install -r requirements.txt

# 4. ACE-Step のクローン
if [ ! -d "$ACESTEP_DIR" ]; then
    echo "ACE-Step v1.5 をクローン中..."
    git clone https://github.com/ace-step/ACE-Step-1.5.git "$ACESTEP_DIR"
else
    echo "  ACE-Step: ${ACESTEP_DIR} に存在"
fi

# 5. ACE-Step 依存パッケージのインストール
echo "ACE-Step 依存パッケージをインストール中..."
cd "$ACESTEP_DIR"
uv sync

# 6. モデルのダウンロード
echo "ACE-Step モデルをダウンロード中（初回は時間がかかります）..."
uv run acestep-download || echo "  モデルダウンロードをスキップ（既に存在する可能性あり）"

# 7. generated_tracks ディレクトリの作成
cd "$PROJECT_DIR"
mkdir -p generated_tracks/lofi generated_tracks/anime generated_tracks/jazz

# 8. .env の作成
if [ ! -f .env ]; then
    cp .env.example .env
    echo "  .env.example から .env を作成しました — パスワードを編集してください"
fi

echo ""
echo "=== セットアップ完了 ==="
echo ""
echo "ACE-Step API サーバーの起動:"
echo "  cd ${ACESTEP_DIR} && uv run acestep-api"
echo ""
echo "ワーカーの起動:"
echo "  cd ${PROJECT_DIR} && source .venv/bin/activate && python -m worker"
echo ""
echo "Docker サービスの起動:"
echo "  cd ${PROJECT_DIR} && docker compose up -d"
