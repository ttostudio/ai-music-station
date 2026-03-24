# Changelog

## [Unreleased]

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
