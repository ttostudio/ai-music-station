# AI Music Station 楽曲共有ページ — 画面仕様書

## 概要
外部ユーザーが共有リンクからアクセスする、楽曲再生＆シェアページ。ダーク系テーマで、モバイル・タブレット・デスクトップに対応。

---

## ページ構成

### 共通要素（全レイアウト）
1. **ステータスバー** — OS制御（62px）
2. **ヘッダー** — 戻るボタン + ページタイトル「楽曲を共有」
3. **メインコンテンツ** — レイアウト別参照
4. **フッター** — なし（スクロール可能）

---

## レイアウト仕様

### モバイル（< 768px）
**幅**: 402px（iPhone標準）

#### レイアウト構成
```
┌─────────────────────────┐
│ ステータスバー (62px)   │
├─────────────────────────┤
│ ← | 楽曲を共有 (56px)   │
├─────────────────────────┤
│                         │
│  アルバムアート (240×240) │
│  ※グラデーション内        │
│                         │
│ Midnight Echoes         │ (20px, 700)
│ AI Music Station        │ (14px, secondary)
│ Anime Channel           │ (12px, muted)
│                         │
│ ┌───────────────────┐   │
│ │  ● (play/pause)   │   │
│ │  ● (next)         │   │
│ │                   │   │
│ │ ▯▯▯▯▯▯▯▯▯▯▯▯▯ │   │
│ │ 0:00       3:24   │   │
│ │                   │   │
│ │ 🔊 ▯▯▯▯▯ 100%   │   │
│ └───────────────────┘   │
│                         │
│ 歌詞 (14px, 600)         │
│ ┌───────────────────┐   │
│ │ Under the         │   │
│ │ moonlight,        │   │
│ │ echoes of...      │   │
│ └───────────────────┘   │
│                         │
│ ┌───────────────────┐   │
│ │ AI Music Station  │   │
│ │ で聴く            │   │
│ └───────────────────┘   │
│                         │
└─────────────────────────┘
```

#### 各セクション寸法
- **アルバムアートコンテナ**: 402px幅, 280px高
  - **アルバムアート**: 240×240, radius: 16px
- **曲情報**: 402px幅
  - 曲名: 20px/bold/white
  - アーティスト: 14px/secondary
  - チャンネル名: 12px/muted
- **プレイヤーセクション**: 402px幅, padding: 16px, radius: 16px, bg: #1A1A2E
  - コントロール行: height 50px, gap 24px
  - プログレスバー: height 4px
  - ボリュームコントロール: height 4px
- **歌詞セクション**: 402px幅, height 120px
- **CTA**: 402px幅, height 48px, radius: 12px

#### パディング・ギャップ
- Content Wrapper: padding [24, 16, 24, 16]
- Content Gap: 24px

---

### タブレット（768px ~ 1023px）
**幅**: 768px

#### レイアウト構成（水平2カラム）
```
┌────────────────────────────────────────┐
│ ← | 楽曲を共有                         │ (56px)
├────────────────────────────────────────┤
│                                        │
│  Album (280×280)   │  曲名 (28px/bold) │
│  ※グラデーション    │                   │
│  内                 │  Anime Channel    │
│                     │                   │
│                     │  ┌──────────────┐ │
│                     │  │ ● ● (control)│ │
│                     │  │              │ │
│                     │  │ Progress     │ │
│                     │  │ 0:00   3:24  │ │
│                     │  │              │ │
│                     │  │ 🔊 Vol  100% │ │
│                     │  └──────────────┘ │
│                     │                   │
│  歌詞をスクロール中  │  CTA Button       │
│                     │                   │
└────────────────────────────────────────┘
```

#### 各セクション寸法
- **左パネル（アルバム）**: 360px
  - **アルバムアート**: 280×280, radius: 16px
  - **ラベル**: "歌詞をスクロール中", 12px/muted
- **右パネル（情報）**: fill_container
  - **曲名**: 28px/bold/white
  - **アーティスト情報**: vertical stack, gap: 4px
  - **プレイヤーセクション**: fill_container, padding: 16px, radius: 16px
  - **CTA**: fill_container, height: 48px

#### パディング・ギャップ
- Wrapper: padding [24, 24, 24, 24], gap: 32px

---

### デスクトップ（≥ 1024px）
**幅**: 1200px

#### レイアウト構成（水平3カラム相当）
```
┌─────────────────────────────────────────────────┐
│ ← | 楽曲を共有                                  │ (56px)
├─────────────────────────────────────────────────┤
│                                                 │
│  Album (360×360)   │  曲名 (36px/bold)         │
│  ※グラデーション    │                           │
│  内                 │  AI Music Station × ...   │
│                     │                           │
│  歌詞をスクロール中  │  ┌───────────────────┐   │
│                     │  │ ● ● ● (controls) │   │
│                     │  │                   │   │
│                     │  │ Progress (6px)    │   │
│                     │  │ 0:00      3:24    │   │
│                     │  │                   │   │
│                     │  │ 🔊 Volume  100%   │   │
│                     │  └───────────────────┘   │
│                     │                           │
│                     │  歌詞 (16px/bold)         │
│                     │  ┌───────────────────┐   │
│                     │  │ Under the         │   │
│                     │  │ moonlight,        │   │
│                     │  │ echoes of...      │   │
│                     │  │ (scrollable)      │   │
│                     │  └───────────────────┘   │
│                     │                           │
│                     │  ┌───────────────────┐   │
│                     │  │ AI Music Station  │   │
│                     │  │ で聴く            │   │
│                     │  └───────────────────┘   │
│                     │                           │
└─────────────────────────────────────────────────┘
```

#### 各セクション寸法
- **左パネル（アルバム）**: 400px
  - **アルバムアート**: 360×360, radius: 16px
  - **ラベル**: "歌詞をスクロール中", 12px/muted
- **右パネル（情報）**: fill_container, gap: 32px
  - **タイトル**: 36px/bold/white
  - **アーティスト情報**:
    - Artist: 16px/secondary
    - Channel: 14px/muted
  - **プレイヤーセクション**: fill_container, padding: 24px, gap: 16px, radius: 16px
    - Controls: height 56px, gap: 40px
    - Progress: height 6px
    - Volume: height 6px
  - **歌詞セクション**: fill_container, height: 200px
  - **CTA**: fill_container, height: 52px

#### パディング・ギャップ
- Wrapper: padding [40, 40, 40, 40], gap: 60px

---

## デザイントークン

### カラー
| 用途 | 値 | 使用箇所 |
|------|-----|---------|
| **背景（ベース）** | #0A0A0F | ページ背景、ステータスバー |
| **背景（カード）** | #1A1A2E | プレイヤーセクション、歌詞ボックス |
| **テキスト（プライマリ）** | #FFFFFF | 曲名、ボタンテキスト |
| **テキスト（セカンダリ）** | #8B8BA0 | アーティスト名、時間表示 |
| **テキスト（ミュート）** | #6B6B80 | チャンネル名、ラベル |
| **アクセント** | #6366f1 | 戻るボタン、プログレスバー |
| **グラデーション（CTA）** | #6366f1 → #a855f7 | CTAボタン |

### タイポグラフィ
| サイズ | 用途 | 重さ | 行高 |
|--------|------|------|------|
| **36px** | デスクトップ曲名 | 700 | 1.2 |
| **28px** | タブレット曲名 | 700 | 1.2 |
| **20px** | モバイル曲名 | 700 | 1.2 |
| **18px** | 見出し（デスクトップ） | 600 | 1.2 |
| **16px** | セクション見出し | 600 | 1.4 |
| **14px** | 本文、ボタン | 400/600 | 1.4 |
| **12px** | メタ情報 | 400 | 1.4 |
| **11px** | 小さいテキスト | 400 | 1.4 |

### スペーシング
| 値 | 用途 |
|----|------|
| **40px** | デスクトップ padding |
| **24px** | タブレット padding、gap |
| **16px** | モバイル padding、component gap |
| **32px** | デスクトップ gap |
| **12px** | 要素内 gap |
| **8px** | 小さい gap |

### ラディウス
| 値 | 用途 |
|----|------|
| **16px** | アルバムアート、パネル |
| **12px** | 歌詞ボックス |
| **25-28px** | ボタン（半円） |
| **2-3px** | プログレスバー |

---

## コンポーネント仕様

### プレイヤーセクション
- **背景**: #1A1A2E
- **ラディウス**: 16px
- **内部ギャップ**: 16px
- **パディング**: 16px (mobile), 24px (desktop)

#### コントロール行
- **高さ**: 50px (mobile), 56px (desktop)
- **アイテム**: 2～3個の円形ボタン（直径 50px / 56px）
- **ギャップ**: 24px (mobile), 40px (desktop)

#### プログレスバー
- **高さ**: 4px (mobile), 6px (desktop)
- **背景**: rgba(255,255,255,0.1)
- **フィル**: gradient #6366f1 → #ec4899

#### ボリュームコントロール
- **レイアウト**: horizontal
- **アイテム**: アイコン + スライダー + パーセンテージテキスト
- **高さ**: 4px (mobile), 6px (desktop)

### CTA ボタン
- **背景**: linear-gradient(135deg, #6366f1, #a855f7)
- **高さ**: 48px (mobile/tablet), 52px (desktop)
- **ラディウス**: 12px
- **テキスト**: "AI Music Stationで聴く", 14px (mobile/tablet), 16px (desktop), bold, white
- **アクション**: `/stream/{trackId}` へのリンク

---

## OGP メタタグ

```html
<!-- ページタイトル（デフォルト） -->
<meta property="og:title" content="楽曲を共有 - AI Music Station" />

<!-- 動的） -->
<meta property="og:title" content="{曲名} - AI Music Station" />

<!-- OGP 画像（固定） -->
<meta property="og:image" content="https://ai-music-station.example.com/og-image.png" width="1200" height="630" />

<!-- 動的（楽曲のサムネイル） -->
<meta property="og:image" content="https://stream.example.com/tracks/{trackId}/thumbnail.png" />

<!-- ページ説明 -->
<meta property="og:description" content="AIが生成した音楽を共有しよう。AI Music Stationで{曲名}を聴く。" />

<!-- ページタイプ -->
<meta property="og:type" content="music.song" />

<!-- URL -->
<meta property="og:url" content="https://ai-music-station.example.com/share/{shareId}" />

<!-- サイト名 -->
<meta property="og:site_name" content="AI Music Station" />

<!-- Twitter Card -->
<meta name="twitter:card" content="summary_large_image" />
<meta name="twitter:title" content="{曲名} - AI Music Station" />
<meta name="twitter:description" content="AIが生成した音楽を共有しよう。{曲名}を聴く。" />
<meta name="twitter:image" content="https://stream.example.com/tracks/{trackId}/thumbnail.png" />
```

---

## インタラクション

### 再生 / 一時停止
- **アクション**: コントロール内の再生ボタンをクリック
- **ビジュアル**: ボタンのアイコンが再生 ↔ 一時停止 に変更
- **音声**: オーディオコンテキスト開始 → ストリーミング再生開始

### ボリューム調整
- **アクション**: ボリュームスライダーをドラッグ
- **ビジュアル**: パーセンテージが 0-100 で更新
- **アクセシビリティ**: キーボード操作対応（上下矢印キー）

### 歌詞スクロール
- **スマートフォン**: タップで歌詞セクションを展開 → スクロール可能
- **デスクトップ**: 歌詞ボックス内で自動スクロール
- **対応形式**: LRC フォーマット（TS タイムスタンプ同期）

### シェア機能
- **アクション**: ページ共有時にOGPメタタグを使用
- **SNSプレビュー**: 曲名 + アルバムアート + チャンネル名表示

### CTA ボタン
- **アクション**: クリック → `/stream/{trackId}` へ遷移
- **目的**: ユーザーをメインアプリにリンク

---

## レスポンシブ ブレークポイント

```typescript
type Breakpoint = "mobile" | "tablet" | "desktop";

const BREAKPOINTS = {
  mobile: { min: 0, max: 767 },    // < 768px
  tablet: { min: 768, max: 1023 }, // 768px ~ 1023px
  desktop: { min: 1024 },          // >= 1024px
};
```

---

## アクセプタンス・クライテリア

- [ ] AC1: モバイル（<768px）でレイアウトがコンテンツを正しく積み重ねる
- [ ] AC2: タブレット（768-1023px）で左右2カラムレイアウトが表示される
- [ ] AC3: デスクトップ（≥1024px）で歌詞がサイドパネルに表示される
- [ ] AC4: すべてのテキストが指定フォントサイズ・色で表示される
- [ ] AC5: グラデーション（アルバムアート・CTA）が正しく描画される
- [ ] AC6: プレイヤーコントロール（再生/一時停止/ボリューム）が機能する
- [ ] AC7: LRC歌詞が存在する場合、歌詞セクションにタイムスタンプ同期で表示される
- [ ] AC8: CTAボタンが `/stream/{trackId}` にリンクする
- [ ] AC9: OGPメタタグがSNSプレビューで正しく表示される（og:title, og:image, og:description）
- [ ] AC10: ページがダークモード（#0A0A0F 背景）でレンダリングされる

---

## デザインファイル

**ファイル**: `.pen` ファイル（Pencil MCP）
- **Mobile**: Share Page - Mobile (402px)
- **Tablet**: Share Page - Tablet (768px)
- **Desktop**: Share Page - Desktop (1200px)

---

## 実装上の注意

1. **Gradient**: 線形グラデーション、rotation: 135度
2. **Typography**: Inter フォントファミリーを使用
3. **Audio**: HTML5 `<audio>` element + crossOrigin="anonymous"
4. **LRC Parser**: 既存の `src/utils/lrc-parser.ts` を活用
5. **SSR/SEO**: OGPタグはサーバーサイドで動的に生成

---

**作成日**: 2026-03-24
**Designer**: ttoClaw UI/UX Designer
**Status**: Design Complete ✓
