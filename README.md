# AI Music Station

ACE-Step v1.5 を搭載したAI音楽生成＆ストリーミングサービス。チャンネル別に楽曲をリクエストし、ラジオのようにブラウザで視聴できます。

## 主な機能

- **AI楽曲生成**: 雰囲気を伝えるだけで歌詞・曲名・ボーカル付き楽曲を自動生成（claude CLI + ACE-Step）
- **ラジオストリーミング**: チャンネル別に24時間配信（Icecast2 + Liquidsoap）
- **カラオケ歌詞（LRC）**: 再生中の歌詞をリアルタイムでカラオケ表示
- **レスポンシブUI**: モバイル / タブレット / PC 3段階の最適化レイアウト
- **共有リンク・OGP**: トラックをSNSシェア可能なURL発行、OGPサムネイル自動生成
- **再生トラッキング**: ハッシュ化IPによるプライバシーフレンドリーな再生統計
- **フィードバック**: 👍リアクションでお気に入りを記録、重み付きシャッフルで人気曲を優先再生
- **自動運用**: チャンネルストック監視 + 不人気曲の自動棚卸し

## チャンネル

| チャンネル | スタイル | BPM | 長さ |
|-----------|---------|-----|------|
| Anime Songs（アニソン） | J-pop アニメオープニング・エンディングテーマ | 120-160 | 90秒 |
| えぐしゅぎ | 中毒性の強い過激なJ-pop／アニメソング | — | — |
| Game Music（ゲームミュージック） | RPG・アクションゲームBGM | — | — |
| Jazz Station（ジャズステーション） | スムースジャズ、即興演奏 | 100-140 | 240秒 |
| AI Podcast | AI Tech Blog 記事の音声ポッドキャスト | — | — |

## アーキテクチャ

```
ブラウザ → Caddy (:3200) → フロントエンド (React SPA)
                          → /api/* → FastAPI (:8000)
                          → /stream/* → Icecast2 (:8000)
                          → /share/* → OGP HTMLページ

Icecast2 ← Liquidsoap (チャンネル毎に1つ、playlist.m3u から再生)
FastAPI ← PostgreSQL (:5432) ← ワーカー (ホストネイティブ Python プロセス)
ワーカー → ACE-Step API (:8001, ホストネイティブ MLX) → FLAC → ./generated_tracks/
        → claude CLI（歌詞・曲名生成、ローカル）
        → プレイリスト生成（5分間隔）/ 棚卸し（10分間隔）/ 自動生成（60秒間隔）
```

### サービス一覧

| サービス | 実行環境 | 説明 |
|---------|---------|------|
| `postgres` | Docker | PostgreSQL 16 — キュー、メタデータ、チャンネル |
| `api` | Docker | FastAPI — REST API |
| `icecast` | Docker | Icecast2 — オーディオストリーミング |
| `liquidsoap` | Docker | Liquidsoap — playlist.m3u 再生、Icecast 配信 |
| `frontend` | Docker | React SPA (nginx) |
| `caddy` | Docker | リバースプロキシ (ポート 3200) |
| `worker` | ホスト | ACE-Step キューコンシューマー + 自動生成ジョブ (Apple Silicon) |

## クイックスタート

### 1. クローンと設定

```bash
git clone https://github.com/ttostudio/ai-music-station.git
cd ai-music-station
cp .env.example .env
# .env を編集してパスワードを設定（claude CLIがインストール済みであること）
```

### 2. Docker サービスの起動

```bash
docker compose up -d
```

PostgreSQL、マイグレーション、チャンネルシード、API、Icecast2 ストリーミング、Liquidsoap、フロントエンド、Caddy リバースプロキシが起動します。

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

## 技術スタック

| カテゴリ | 技術 |
|---------|------|
| 音楽生成 | ACE-Step v1.5 (Apple Silicon MLX) |
| 歌詞生成 | claude CLI（ローカル Claude Code） |
| バックエンド | Python FastAPI + SQLAlchemy + Alembic |
| ストリーミング | Icecast2 + Liquidsoap (OGG Vorbis) |
| フロントエンド | React 19 + Vite + Tailwind CSS |
| データベース | PostgreSQL 16 |
| インフラ | Docker Compose, Caddy |

## API エンドポイント

| メソッド | エンドポイント | 説明 |
|---------|--------------|------|
| GET | `/api/health` | ヘルスチェック |
| GET | `/api/channels` | チャンネル一覧 |
| GET | `/api/channels/{slug}` | チャンネル詳細 |
| POST | `/api/channels/{slug}/requests` | 楽曲リクエスト送信 |
| GET | `/api/channels/{slug}/tracks` | 生成済みトラック一覧 |
| GET | `/api/channels/{slug}/now-playing` | 再生中のトラック（LRC歌詞含む） |
| POST | `/api/tracks/{id}/reactions` | 👍リアクション追加 |
| DELETE | `/api/tracks/{id}/reactions` | リアクション取消 |
| GET | `/api/tracks/{id}/reactions` | リアクション状態取得 |
| POST | `/api/shares` | 共有リンク発行 |
| GET | `/api/shares/{token}` | OGPページ返却 |
| POST | `/api/analytics/play` | 再生イベント記録 |

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
docker compose config  # 設定検証
```

## ライセンス

MIT — 詳細は [LICENSE](LICENSE) を参照してください。
