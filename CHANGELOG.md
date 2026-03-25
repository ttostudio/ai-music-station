# Changelog

## [Unreleased]

### Added (Issue #9 — ACE-Step 音楽生成統合)
- `api/services/acestep_client.py`: ACE-Step REST API 正式クライアント
  - `AceStepClient.submit_job()` — POST /release_task でジョブ投入
  - `AceStepClient.poll_result()` — POST /query_result でポーリング
  - `AceStepClient.download_audio()` — GET /v1/audio で音声ダウンロード
  - ステータスマッピング: ACE-Step `success` → 内部 `completed`
  - 入力サニタイザー（prompt / lyrics / bpm / duration / music_key / vocal_language）
- `api/services/generation_worker.py`: FastAPI lifespan から起動するバックグラウンドワーカー
- `api/routers/generate.py`: 新規エンドポイント
  - `POST /api/generate` — 生成リクエスト投入（チャンネル横断）
  - `GET /api/generate/{request_id}/status` — ステータス確認
  - `GET /api/channels/{slug}/generate-status` — チャンネルキュー状況
- DB マイグレーション `007_acestep_columns`:
  - `requests` テーブル: `ace_step_job_id`, `ace_step_submitted_at`, `ace_step_poll_count` 追加
  - `tracks` テーブル: `generation_model`, `ace_step_job_id` 追加
- `docker-compose.yml`: `ACESTEP_API_URL` 環境変数、`extra_hosts: host.docker.internal:host-gateway` 追加

### Changed (Issue #9)
- `worker/acestep_client.py`: 誤った OpenRouter 互換実装を api/services クライアントへの互換シムに置換
- `worker/queue_consumer.py`: generate() 単一呼び出しから submit_job → poll_result → download_audio の非同期フローに変更
- `worker/models.py`: Request / Track モデルに ACE-Step 関連フィールド追加
- `worker/config.py`: `ACESTEP_API_URL` デフォルトを `http://host.docker.internal:8001` に変更、ポーリング設定追加
- `api/main.py`: generate ルーター登録、lifespan で生成ワーカー起動

### Security
- 内部 API 認証導入: POST /internal/* に Bearer Token 認証を追加（環境変数 INTERNAL_API_KEY）
- 認証なしリクエストは 401 Unauthorized を返す

### Added
- 共有リンク API（POST /api/tracks/{id}/share — idempotent トークン発行）
- OGP メタタグ付き共有ページ（GET /share/{token} — SSR HTML）
- 再生トラッキング API（POST /api/analytics/play — fire-and-forget）
- トラック統計 API（GET /api/analytics/tracks/{id}/stats）
- DB: share_links テーブル（共有トークン管理）
- DB: track_analytics テーブル（再生・閲覧イベント記録）
- Caddy: /share/* ルート追加（FastAPI へプロキシ）
- セキュリティ: IP ハッシュ化（SHA-256 + ソルト）、HTML エスケープ、入力バリデーション
- 環境変数: PUBLIC_BASE_URL, ANALYTICS_IP_SALT
- モバイルレスポンシブレイアウト（タブバー + 画面遷移型）
- PC/タブレット横シアター型レイアウト（フローティングバー + チャンネルメニュー + 歌詞パネル）
- タブレット縦持ちレイアウト（上下分割）
- 新規コンポーネント: TabBar, MiniPlayer, FloatingBar, ChannelMenu, NowPlayingScreen, KaraokeScreen, HomeScreen, LikesScreen, TheaterLayout, TabletLayout, MobileLayout, ActionButtons, PlaybackControls, ProgressBar, ChannelIcon
- useBreakpoint フック（レスポンシブ切り替え）
- LRCパーサーユーティリティ
- カラオケオーバーレイ（PC: 白+グロウ / モバイル: ゴールド）
- チャンネル別テーマカラー（5チャンネル対応）
- デザイントークン（CSS Custom Properties 80+）

### Changed
- App.tsx: ルーティング/状態管理をレスポンシブ対応に改修
- styles.css: デザイントークン追加、新レイアウト用スタイル
- ChannelSelector: popup/gridモード対応
- LyricsDisplay: pc-overlay/tablet-bottomモード対応

### Fixed
- N/A

### Removed
- 旧2カラムグリッドレイアウト
