# Changelog

## [Unreleased]

### Added
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
