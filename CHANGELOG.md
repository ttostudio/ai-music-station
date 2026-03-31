# Changelog

## [Unreleased]

### Added (Issue #86 — bossanova/classical/electronic チャンネル無音問題の解消)
- `scripts/fix_empty_channels.py`: 無音チャンネル修正スクリプト
  - Step 1: bossanova/classical/electronic のファントムレコード（ファイル未存在）を `is_retired=true` に更新
  - Step 2: jazz→bossanova(10曲), game→classical(10曲), egushugi+lofi→electronic(各5曲) クロスチャンネル再配置（実ファイルコピー）
  - Step 3: 各チャンネルの playlist.m3u を更新
  - Step 4: ACE-Step 停止中のため対象チャンネルの `auto_generate=false` に設定
  - `--dry-run` オプション対応
  - 再配置トラックには `generation_model='cross-channel-reuse'` を付与（ACE-Step 復旧後の識別用）
- `scripts/channel_health_check.py`: チャンネルDB/ファイル整合性ヘルスチェックスクリプト
  - 全チャンネルの DB アクティブ数・ファイル数・ファントム数・プレイリストエントリ数を一覧表示
  - `--channel SLUG` で特定チャンネルのみ検証
  - `--fail-on-mismatch` で不整合時に exit code 1 で終了（CI 連携用）
  - `docker exec product-ai-music-station-api-1 python -m scripts.channel_health_check` で実行

### Added (Issue #85 — トラック品質スコアリング修正)
- `Dockerfile.api`: ffmpeg/ffprobe をインストール（品質スコアリングの動作に必須）
- `scripts/batch_score.py`: 未スコア曲の一括スコアリングスクリプト
  - `docker exec product-ai-music-station-api-1 python -m scripts.batch_score` で実行
  - `--dry-run` オプション対応
  - `--concurrency` オプション（デフォルト5並行）
  - 進捗表示（processed/total）・完了サマリー
- `scripts/__init__.py`: scripts パッケージ化（`python -m scripts.batch_score` 対応）

### Fixed (Issue #85)
- `api/routers/quality.py`: rescore エンドポイントのファイルパスを相対パスから絶対パスへ修正
  - `track.file_path` → `/tracks/` + `track.file_path`（コンテナ内マウントパス）
- `worker/queue_consumer.py`: 品質スコアリング失敗時のエラーハンドリング改善
  - `logger.warning` → `logger.exception`（スタックトレース付きログ）
  - リトライ機構追加（最大2回、バックオフ1秒、失敗時セッションロールバック）
- `worker/quality_scorer.py`: スコア記録の重複防止（delete-before-insert による UPSERT 相当）

### Added (Phase 2 — フロントエンド: Player デュアルモード・プレイリスト再生・グローバル検索・リクエストキュー)
- `hooks/usePlaylistPlayer.ts`: トラック再生フック (Fisher-Yates シャッフル、リピート、prev/next)
- `components/SearchBar.tsx`: グローバル検索バー (300ms デバウンス、デスクトップ/タブレット/モバイル対応)
- `components/RequestQueueTab.tsx`: 全チャンネル横断リクエストキュータブ (5秒ポーリング、ステータスバッジ)
- `components/FloatingBar.tsx`: モード切替 (Radio ↔ ListMusic)、トラックモード専用コントロール (prev/next/shuffle/repeat/seek)
- `components/MiniPlayer.tsx`: トラックモード対応 (曲名・前/次ボタン・プログレスバー)
- `components/PlaylistTrackItem.tsx`: 再生ボタン追加、再生中トラックのアクティブハイライト
- `components/PlaylistDetail.tsx`: 「全曲再生」「シャッフル」ボタン、トラック行の再生ボタン、onPlayPlaylist/onPlayTrack コールバック
- `components/TabBar.tsx`: QUEUE タブ追加 (5タブ構成)、バッジ表示
- `components/layouts/MobileLayout.tsx`: QUEUEタブ・SearchBar (モバイル展開型)・PlaylistPlayer 連携
- `components/layouts/DesktopLayout.tsx`: SearchBar (右上固定)・PlaylistPlayer 連携
- `components/layouts/TabletLayout.tsx`: SearchBar・PlaylistPlayer 連携
- `App.tsx`: trackAudioRef + usePlaylistPlayer 統合、ストリーム/トラックモード相互停止制御
- `api/types.ts`: PlayMode, RepeatMode, TrackSearchListResponse, AllRequestsListResponse 型追加
- `api/client.ts`: searchTracks(), getTrackAudioUrl(), getAllRequests() 追加
- `styles.css`: Phase 2 デザイントークン (status colors, track-active highlight) + 新コンポーネントスタイル

### Added (Issue #28 — プレイリスト機能)
- プレイリスト CRUD + トラック追加/削除/並べ替え + お気に入り連携
- 9 API エンドポイント、6 新規 FE コンポーネント、@dnd-kit ドラッグ&ドロップ
- QMOフルサイクル開発（全10ロール配置）


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
