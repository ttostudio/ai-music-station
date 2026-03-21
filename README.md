# AI Music Station

ACE-Step v1.5 を搭載した音楽生成＆ストリーミングサービス。チャンネル別（アニソン、LoFi、ジャズ）に楽曲をリクエストし、ラジオのようにブラウザで視聴できます。

## アーキテクチャ

```
ブラウザ → Caddy (:3200) → フロントエンド (React SPA)
                          → /api/* → FastAPI (:8000)
                          → /stream/* → Icecast2 (:8000)

Icecast2 ← Liquidsoap (チャンネル毎に1つ、共有ボリュームからFLACを読み取り)
FastAPI ← PostgreSQL (:5432) ← ワーカー (ホストネイティブ Python プロセス)
ワーカー → ACE-Step API (:8001, ホストネイティブ MLX) → FLAC → ./generated_tracks/
```

### サービス一覧

| サービス | 実行環境 | 説明 |
|---------|---------|------|
| `postgres` | Docker | PostgreSQL 16 — キュー、メタデータ、チャンネル |
| `api` | Docker | FastAPI — REST API |
| `icecast` | Docker | Icecast2 — オーディオストリーミング |
| `liquidsoap-{lofi,anime,jazz}` | Docker | Liquidsoap — トラック読み取り、Icecast 配信 |
| `frontend` | Docker | React SPA (nginx) |
| `caddy` | Docker | リバースプロキシ (ポート 3200) |
| `worker` | ホスト | ACE-Step キューコンシューマー (Apple Silicon) |

## クイックスタート

### 1. クローンと設定

```bash
git clone https://github.com/ttostudio/ai-music-station.git
cd ai-music-station
cp .env.example .env
# .env を編集してパスワードを設定
```

### 2. Docker サービスの起動

```bash
docker compose up -d
```

PostgreSQL、マイグレーション、チャンネルシード、API、Icecast2 ストリーミング、チャンネル毎の Liquidsoap、フロントエンド、Caddy リバースプロキシが起動します。

### 3. ワーカーのセットアップ（Apple Silicon ホスト）

音楽生成ワーカーは MPS/MLX GPU アクセスのためホスト Mac mini で実行します：

```bash
# セットアップスクリプトの実行（Python 3.12 仮想環境を自動作成）
./scripts/setup-worker.sh

# ACE-Step API サーバーの起動（別ターミナルで）
cd ~/ace-step && uv run acestep-api

# ワーカーの起動
source .venv/bin/activate && python -m worker
```

### 4. プレーヤーを開く

ブラウザで **http://localhost:3200** にアクセスしてください。

## チャンネル

| チャンネル | スタイル | BPM | 長さ |
|-----------|---------|-----|------|
| LoFi ビーツ | チルなローファイ・ヒップホップ | 70-90 | 180秒 |
| アニソン | J-pop アニメテーマ | 120-160 | 90秒 |
| ジャズステーション | スムースジャズ | 100-140 | 240秒 |

## API エンドポイント

| メソッド | エンドポイント | 説明 |
|---------|--------------|------|
| GET | `/api/health` | ヘルスチェック |
| GET | `/api/channels` | チャンネル一覧 |
| GET | `/api/channels/{slug}` | チャンネル詳細 |
| POST | `/api/channels/{slug}/requests` | 楽曲リクエスト送信 |
| GET | `/api/channels/{slug}/tracks` | 生成済みトラック一覧 |
| GET | `/api/channels/{slug}/now-playing` | 再生中のトラック |

## 開発

```bash
# Python
pip install -r requirements.txt
ruff check .
pytest

# フロントエンド
cd frontend && npm ci
npm run lint
npm test

# Docker
docker compose config  # 検証
```

## 技術スタック

- **音楽生成:** ACE-Step v1.5 (Apple Silicon MLX)
- **バックエンド:** Python FastAPI + SQLAlchemy + Alembic
- **ストリーミング:** Icecast2 + Liquidsoap (OGG Vorbis)
- **フロントエンド:** React 19 + Vite + Tailwind CSS
- **データベース:** PostgreSQL 16
- **インフラ:** Docker Compose, Caddy

## ライセンス

MIT — 詳細は [LICENSE](LICENSE) を参照してください。
