# AI Music Station — ソフトウェア設計書

## 1. 概要

AI Music Station は、Apple Silicon 上で ACE-Step v1.5 を使用して音楽を生成し、ラジオステーションのようにストリーミング配信する Web アプリケーションです。ユーザーはチャンネル（LoFi、アニソン、ジャズなど）を選択し、楽曲をリクエストして、ブラウザで連続オーディオストリームを視聴できます。

## 2. アーキテクチャ

```
ブラウザ → Caddy (:3200) → フロントエンド (React SPA, nginx)
                          → /api/* → FastAPI (:8000)
                          → /stream/* → Icecast2 (:8000)

Icecast2 ← Liquidsoap (チャンネル毎に1つ、共有ボリュームからFLACを読み取り)
FastAPI ← PostgreSQL (:5432) ← ワーカー (ホストネイティブ Python プロセス)
ワーカー → ACE-Step REST API (:8001, ホストネイティブ MLX/MPS) → FLAC → ./generated_tracks/
```

### サービス一覧

| サービス | 実行環境 | ポート | 説明 |
|---------|---------|-------|------|
| postgres | Docker | 5432 | PostgreSQL 16 — キュー、メタデータ、チャンネル |
| api | Docker | 8000 | FastAPI — REST API |
| icecast | Docker | 8000 | Icecast2 — オーディオストリーミングサーバー |
| liquidsoap-{channel} | Docker | — | Liquidsoap — トラック読み取り、Icecast マウント配信 |
| frontend | Docker | 80 | React SPA (nginx 配信) |
| caddy | Docker | 3200 | リバースプロキシ（エントリポイント） |
| migrate | Docker | — | Alembic マイグレーションランナー（1回実行） |
| worker | ホスト | — | ACE-Step キューコンシューマー (Apple Silicon ネイティブ) |
| ace-step | ホスト | 8001 | ACE-Step REST API (`uv run acestep-api`) |

## 3. データベーススキーマ

### channels テーブル

| カラム | 型 | 説明 |
|--------|------|------|
| id | UUID PK | |
| slug | VARCHAR(50) UNIQUE | URL セーフ識別子（例: "lofi"） |
| name | VARCHAR(100) | 表示名（例: "LoFi ビーツ"） |
| description | TEXT | チャンネル説明 |
| is_active | BOOLEAN | リクエスト受付可否 |
| default_bpm_min | INTEGER | 生成時の最小 BPM |
| default_bpm_max | INTEGER | 生成時の最大 BPM |
| default_duration | INTEGER | デフォルトトラック長（秒） |
| default_key | VARCHAR(10) | デフォルト音楽キー |
| default_instrumental | BOOLEAN | デフォルトインスト設定 |
| prompt_template | TEXT | ACE-Step 用ベースキャプションテンプレート |
| vocal_language | VARCHAR(10) | 言語コード（例: "ja", "en"） |
| created_at | TIMESTAMPTZ | |
| updated_at | TIMESTAMPTZ | |

### requests テーブル

| カラム | 型 | 説明 |
|--------|------|------|
| id | UUID PK | |
| channel_id | UUID FK→channels | |
| status | VARCHAR(20) | pending → processing → completed / failed |
| caption | TEXT | ユーザー提供の説明 |
| lyrics | TEXT | ユーザー提供の歌詞 |
| bpm | INTEGER | リクエスト BPM オーバーライド |
| duration | INTEGER | リクエスト長オーバーライド（秒） |
| music_key | VARCHAR(10) | リクエストキーオーバーライド |
| worker_id | VARCHAR(100) | 処理中ワーカーのホスト名 |
| started_at | TIMESTAMPTZ | 処理開始時刻 |
| completed_at | TIMESTAMPTZ | 処理完了時刻 |
| error_message | TEXT | 失敗時のエラー詳細 |
| created_at | TIMESTAMPTZ | |
| updated_at | TIMESTAMPTZ | |

### tracks テーブル

| カラム | 型 | 説明 |
|--------|------|------|
| id | UUID PK | |
| request_id | UUID FK→requests (UNIQUE) | |
| channel_id | UUID FK→channels | |
| file_path | VARCHAR(500) | generated_tracks/ 内の相対パス |
| file_size | BIGINT | ファイルサイズ（バイト） |
| duration_ms | INTEGER | 実際のオーディオ長 |
| sample_rate | INTEGER | サンプルレート（デフォルト 48000） |
| caption | TEXT | ACE-Step に送信した実際のキャプション |
| lyrics | TEXT | 実際の歌詞 |
| bpm | INTEGER | 実際の BPM |
| music_key | VARCHAR(10) | 実際のキー |
| instrumental | BOOLEAN | インストかどうか |
| num_steps | INTEGER | デノイジングステップ数 |
| cfg_scale | FLOAT | CFG スケール |
| seed | BIGINT | ランダムシード |
| play_count | INTEGER | ストリーム再生回数 |
| last_played_at | TIMESTAMPTZ | |
| created_at | TIMESTAMPTZ | |

### now_playing テーブル

| カラム | 型 | 説明 |
|--------|------|------|
| channel_id | UUID PK FK→channels | |
| track_id | UUID FK→tracks | |
| started_at | TIMESTAMPTZ | トラック再生開始時刻 |

### インデックス

- `idx_requests_pending` — `(status, created_at) WHERE status = 'pending'`
- `idx_requests_channel` — `(channel_id, status)`
- `idx_tracks_channel` — `(channel_id, created_at DESC)`

## 4. API コントラクト

ベース URL: `/api`

### ヘルスチェック

```
GET /api/health → 200
{
  "status": "正常",
  "database": "接続済み",
  "channels_active": 3
}
```

### チャンネル

```
GET /api/channels → 200
{
  "channels": [{
    "id": "uuid", "slug": "lofi", "name": "LoFi ビーツ",
    "description": "...", "is_active": true,
    "queue_depth": 3, "total_tracks": 42,
    "stream_url": "/stream/lofi.ogg",
    "now_playing": { "track_id": "uuid", "caption": "...", "started_at": "ISO8601" } | null
  }]
}

GET /api/channels/{slug} → 200 | 404
  上記に加えて default_bpm_min, default_bpm_max, default_duration, default_instrumental を含む
```

### リクエスト

```
POST /api/channels/{slug}/requests → 201 | 404 | 422
Body: { "caption"?: string, "lyrics"?: string, "bpm"?: int, "duration"?: int, "music_key"?: string }
Response: { "id": "uuid", "channel_slug": "lofi", "status": "pending", "position": 4, "created_at": "ISO8601" }

GET /api/channels/{slug}/requests?status=pending&limit=20&offset=0 → 200
{ "requests": [...], "total": 15 }

GET /api/requests/{id} → 200 | 404
{ "id", "channel_slug", "status", "caption", "position", "created_at", "started_at", "completed_at", "track": {...} | null }
```

### トラック

```
GET /api/channels/{slug}/tracks?limit=20&offset=0 → 200
{ "tracks": [{ "id", "caption", "duration_ms", "bpm", "music_key", "instrumental", "play_count", "created_at" }], "total": 42 }

GET /api/channels/{slug}/now-playing → 200
{ "track": { "id", "caption", "duration_ms", "elapsed_ms", "bpm", "music_key" } | null }
```

### 内部エンドポイント（Caddy 経由で非公開）

```
POST /internal/now-playing
Body: { "channel_slug": "lofi", "track_id": "uuid" } → 200

POST /internal/worker-heartbeat
Body: { "worker_id": "macmini-1", "active_request_id": "uuid" | null } → 200
```

## 5. ストリーミングアーキテクチャ

### Icecast2

チャンネル毎のマウントポイント:
- `/lofi.ogg` — OGG Vorbis
- `/anime.ogg` — OGG Vorbis
- `/jazz.ogg` — OGG Vorbis

### Liquidsoap

チャンネル毎に1コンテナ。各コンテナは:
1. `generated_tracks/{channel_slug}/` の FLAC ファイルを監視
2. 自動リロードでプレイリストを管理
3. トラック間のクロスフェード（3秒）
4. トラックがない場合は無音にフォールバック
5. OGG Vorbis にエンコードして Icecast マウントポイントにプッシュ
6. トラック変更時に `/internal/now-playing` を呼び出し

### ブラウザ再生

HTML5 `<audio>` 要素で Caddy 経由の Icecast ストリーム URL を指定:
```
<audio src="/stream/lofi.ogg" />
```

## 6. ACE-Step ワーカー

Mac mini 上でネイティブ実行（Docker 外）、MPS/MLX アクセス用。

### 接続

- PostgreSQL: `localhost:5432`（Docker が公開）
- ACE-Step API: `localhost:8001`（ホストネイティブ `uv run acestep-api`）
- 出力: `./generated_tracks/{channel_slug}/{track_id}.flac`（バインドマウント）

### キュー処理ループ

```
2秒毎:
  SELECT * FROM requests WHERE status='pending'
    ORDER BY created_at
    FOR UPDATE SKIP LOCKED LIMIT 1

  見つかった場合:
    UPDATE status='processing', worker_id=hostname, started_at=now()
    リクエスト + チャンネルプリセットからパラメータ構築
    POST http://localhost:8001/generate → FLAC
    generated_tracks/{channel}/{id}.flac に保存
    tracks テーブルに INSERT
    リクエストの status='completed' に UPDATE

  エラー時:
    status='failed', error_message=str(error) に UPDATE
```

### チャンネルプリセット

| チャンネル | BPM | キー | インスト | 言語 | プロンプトテンプレート |
|-----------|-----|-----|---------|------|---------------------|
| LoFi ビーツ | 70-90 | マイナー | はい | — | "lo-fi hip hop beat, chill, relaxed..." |
| アニソン | 120-160 | メジャー | いいえ | ja | "anime opening theme, energetic, J-pop..." |
| ジャズステーション | 100-140 | 各種 | はい | — | "jazz, smooth, saxophone, piano..." |

## 7. Docker Compose

プロジェクト名: `product-ai-music-station`

サービス: postgres, migrate, api, icecast, liquidsoap-lofi, liquidsoap-anime, liquidsoap-jazz, frontend, caddy

全サービスにヘルスチェックあり。シークレットは `.env` ファイル経由。

### Caddy ルーティング

```
:3200 {
    handle /api/* {
        reverse_proxy api:8000
    }
    handle /stream/* {
        uri strip_prefix /stream
        reverse_proxy icecast:8000
    }
    handle {
        reverse_proxy frontend:80
    }
}
```

## 8. デフォルトチャンネル

| スラッグ | 名前 | 説明 |
|---------|------|------|
| lofi | LoFi ビーツ | リラックス＆勉強用のチルなローファイ・ヒップホップ |
| anime | アニソン | AIが生成したアニメのオープニング＆エンディングテーマ |
| jazz | ジャズステーション | スムースジャズ、即興演奏、クラシックな雰囲気 |
