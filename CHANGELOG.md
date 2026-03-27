# Changelog

## [Unreleased]

### Added (Issue #28 — プレイリスト機能)
- `alembic/versions/009_add_playlists.py`: playlists・playlist_tracks テーブル追加マイグレーション（DR-001: user_id → session_id）
- `worker/models.py`: Playlist、PlaylistTrack SQLAlchemy モデル追加（DR-001: session_id、DR-009: updated_at onupdate）
- `api/schemas.py`: プレイリスト関連 Pydantic スキーマ追加（PlaylistCreateBody, PlaylistResponse, PlaylistDetailResponse, PlaylistListResponse, AddTrackBody[bulk], FavoritesResponse 他）
- `api/routers/playlists.py`: プレイリスト API ルーター新規作成
  - `POST /api/playlists` — プレイリスト作成（重複名・上限チェック付き）
  - `GET /api/playlists` — プレイリスト一覧取得
  - `GET /api/playlists/{playlist_id}` — プレイリスト詳細（quality_score・channel_id含む）
  - `PATCH /api/playlists/{playlist_id}` — プレイリスト名・説明更新
  - `DELETE /api/playlists/{playlist_id}` — プレイリスト削除（204 No Content）
  - `POST /api/playlists/{playlist_id}/tracks` — トラック一括追加（track_ids配列、重複・上限チェック付き）
  - `DELETE /api/playlists/{playlist_id}/tracks/{track_id}` — トラック削除（204 No Content、position 自動詰め）
  - `PUT /api/playlists/{playlist_id}/tracks/reorder` — トラック順序一括更新
  - `GET /api/favorites` — お気に入り（like）トラック一覧取得
- `api/main.py`: playlists ルーターを登録

### Added (Issue #20 — リクエスト UI + チャンネル追加)
- `alembic/versions/008_add_channels.py`: 新チャンネル3つ追加
  - `classical`（クラシック）— ピアノ・オーケストラ、BPM 60-120
  - `electronic`（エレクトロニカ）— シンセ・アンビエント、BPM 110-150
  - `bossanova`（ボサノバ）— ブラジルジャズ、BPM 80-110、日本語ボーカル
- `frontend/src/components/RequestForm.tsx`: リクエストフォーム全面刷新
  - チャンネル選択ドロップダウン
  - ムード選択ピル（明るい / 落ち着いた / エネルギッシュ / 哀愁）
  - 任意プロンプト入力テキストエリア
  - `POST /api/generate` に送信
  - 送信後に `RequestHistory` でステータス表示
- `frontend/src/components/RequestHistory.tsx`: リクエスト履歴コンポーネント（新規）
  - `GET /api/generate/{id}/status` を 5 秒ごとにポーリング
  - ステータス表示（待機中 / 生成中 / 完了 / 失敗）+ キュー順位
- `frontend/src/api/types.ts`: `GenerateRequestBody`, `RequestDetailResponse` 型追加
- `frontend/src/api/client.ts`: `submitGenerate()`, `getGenerateStatus()` 関数追加
- `frontend/src/styles.css`: ムードピル・ステータスバッジ・デスクトップリクエストパネルの CSS 追加
- `MobileLayout.tsx`: ラジオタブのチャンネルグリッド下にリクエストフォームを統合
- `TabletLayout.tsx`: 下部セクションにリクエストフォームを統合
- `DesktopLayout.tsx`: 固定トグルボタン + フローティングパネルでリクエストフォームを統合

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
