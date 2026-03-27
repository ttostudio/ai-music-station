# UI/UX 設計書 — プレイリスト機能

**バージョン**: 1.0
**作成日**: 2026-03-27
**担当**: Designer

---

## 1. デザイントークン（既存コードとの整合性確認済み）

> 出典: `frontend/src/styles.css`（直接読み込み確認済み）

### カラー
| トークン | 値 | 用途 |
|---------|-----|------|
| `--color-bg-base` | `#0A0A0F` | ページ背景 |
| `--color-bg-card` | `#1A1A2E` | カード背景 |
| `--color-bg-card-alt` | `#1E1E30` | カード背景（交互） |
| `--color-bg-deep` | `#0F0F1A` | 深い背景（モーダルオーバーレイ） |
| `--color-text-primary` | `#FFFFFF` | 主テキスト |
| `--color-text-secondary` | `#8B8BA0` | 副テキスト |
| `--color-text-muted` | `#6B6B80` | ミュートテキスト |
| `--color-accent` | `#6366f1` | アクセント（インジゴ） |
| `--color-accent-glow` | `rgba(99,102,241,0.3)` | アクセントグロー |
| `--color-border-subtle` | `rgba(255,255,255,0.06)` | ボーダー（薄） |
| `--color-border-dim` | `rgba(255,255,255,0.08)` | ボーダー（中） |
| `--gradient-play-btn` | `linear-gradient(135deg, #6366f1, #a855f7)` | 再生ボタン |
| `--gradient-progress` | `linear-gradient(90deg, #6366f1, #ec4899)` | プログレスバー |

### タイポグラフィ
| トークン | 値 |
|---------|-----|
| `--font-family` | `'Inter', system-ui, sans-serif` |
| `--text-xs` | `10px` |
| `--text-sm` | `11px` |
| `--text-base` | `13px` |
| `--text-md` | `14px` |
| `--text-lg` | `15px` |
| `--text-xl` | `18px` |
| `--text-2xl` | `22px` |

### スペーシング
| トークン | 値 |
|---------|-----|
| `--space-1` | `4px` |
| `--space-2` | `8px` |
| `--space-3` | `12px` |
| `--space-4` | `16px` |
| `--space-5` | `20px` |
| `--space-6` | `24px` |
| `--space-8` | `32px` |

### ボーダーラジウス
| トークン | 値 |
|---------|-----|
| `--radius-card` | `16px` |
| `--radius-btn-lg` | `9999px` |
| `--radius-chip` | `9999px` |
| `--radius-panel` | `20px` |
| `--radius-panel-lg` | `24px` |

### z-index
| トークン | 値 | 対象 |
|---------|-----|------|
| `--z-floating-bar` | `50` | MiniPlayer / FloatingBar |
| `--z-modal` | `60` | モーダル（プレイリスト作成・トラック追加） |

### ブレークポイント
> 出典: `frontend/src/hooks/useBreakpoint.ts` — 実装確認のため参照

```
mobile:  < 768px
tablet:  768px - 1023px
desktop: >= 1024px
```

---

## 2. 既存UIアーキテクチャとの統合ポイント

### 現在の画面遷移モデル（`App.tsx` 確認済み）

```
activeTab: "radio" | "tracks" | "likes"
currentScreen: "home" | "nowplaying" | "karaoke" | "manager"
```

### 追加する値

```
activeTab: "radio" | "tracks" | "likes" | "playlist"  ← 追加
currentScreen: "home" | "nowplaying" | "karaoke" | "manager" | "playlist-detail"  ← 追加
```

### TabBar 変更内容（`TabBar.tsx` 確認済み）
- 既存: Radio / Tracks / Likes（3タブ）
- 変更後: Radio / Tracks / Likes / Playlist（4タブ）
- 追加アイコン: `ListVideo`（lucide-react）
- ラベル: `PLAYLISTS`

---

## 3. 画面ワイヤーフレーム

### 3.1 プレイリスト一覧画面（`activeTab === "playlist"` 時）

**モバイル（< 768px）**

```
┌─────────────────────────────────┐  height: 100vh - 56px(TabBar) - 64px(MiniPlayer)
│  マイプレイリスト           [+]  │  ← header: px-4 py-4
│                                 │     h1: text-xl font-bold
│  ┌─────────────────────────┐   │
│  │ 🎵 お気に入りJ-POP      │   │  ← playlist-card: bg-card radius-card p-4
│  │   12曲 · 最終更新 3/27  │   │     border: color-border-dim
│  │                    ▶    │   │     play btn: right align, gradient-play-btn
│  └─────────────────────────┘   │     size 40x40 radius-btn-lg
│  ┌─────────────────────────┐   │
│  │ 🎮 ゲームBGM集          │   │
│  │   8曲 · 最終更新 3/25   │   │
│  │                    ▶    │   │
│  └─────────────────────────┘   │
│                                 │
│  ┌── 空の状態 ─────────────┐   │
│  │   📋                    │   │  ← empty state（プレイリスト0件時）
│  │   プレイリストがありません │   │     text-center, text-muted
│  │   [新しいプレイリストを   │   │     btn: accent color, radius-btn-lg
│  │    作成]                │   │
│  └─────────────────────────┘   │
└─────────────────────────────────┘
```

**[+] ボタン**: 右上固定、`+` アイコン（lucide-react `Plus`）、accent色、タップでプレイリスト作成モーダル表示

---

### 3.2 プレイリスト詳細画面（`currentScreen === "playlist-detail"` 時）

フルスクリーンオーバーレイ（NowPlayingScreen と同じパターン）

```
┌─────────────────────────────────┐
│  ← 戻る          [編集] [削除]  │  ← header: px-4 py-3, bg-bg-deep
│                                 │     戻る: ChevronLeft icon, text-secondary
│  ┌─────────────────────────┐   │
│  │  [🎵 プレイリストカバー] │   │  ← cover area: 120x120px, radius-card
│  │                         │   │     bg-bg-card, accent gradient border
│  └─────────────────────────┘   │
│                                 │
│  お気に入りJ-POP                │  ← name: text-2xl font-bold
│  12曲 · 45分                   │  ← meta: text-sm text-secondary
│  おすすめの曲を集めました       │  ← description: text-base text-muted
│                                 │
│  [▶ すべて再生]  [シャッフル]  │  ← 2ボタン横並び
│                                 │     再生: gradient-play-btn, radius-btn-lg, h-10
│  ─────────────────────────────  │     シャッフル: bg-bg-card, radius-btn-lg, h-10
│                                 │
│  トラックリスト        [+ 追加] │  ← section header: text-md font-semibold
│                                 │
│  ≡ 1. トラックタイトル    ⋮   │  ← track-item: height 56px
│      アーティスト · 3:45   🗑   │     ≡ ドラッグハンドル（GripVertical icon）
│  ≡ 2. トラックタイトル    ⋮   │     ⋮ メニュー（削除、再生等）
│      アーティスト · 4:12   🗑   │     ドラッグ中: bg-bg-card-alt, shadow-float
│  ≡ 3. ...                      │
│                                 │
└─────────────────────────────────┘
```

**ドラッグ&ドロップ**: `@dnd-kit/core` + `@dnd-kit/sortable` 使用推奨
ドラッグ中トラックは `opacity: 0.5`、ドロップ先はハイライト（`color-border-accent`）

---

### 3.3 プレイリスト作成/編集モーダル

z-index: `--z-modal` (60)、背景オーバーレイ: `rgba(0,0,0,0.7)`

```
┌─────────────────────────────────┐
│ ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░ │  ← backdrop: rgba(0,0,0,0.7)
│ ░  ┌───────────────────────┐  ░ │
│ ░  │ プレイリストを作成 [×] │  ░ │  ← modal: bg-bg-card, radius-panel-lg (24px)
│ ░  │                       │  ░ │     padding: space-6 (24px)
│ ░  │ 名前 *                │  ░ │     width: calc(100% - 32px), max-width: 480px
│ ░  │ ┌───────────────────┐ │  ░ │
│ ░  │ │ プレイリスト名     │ │  ░ │  ← input: bg-bg-deep, radius-card (16px)
│ ░  │ └───────────────────┘ │  ░ │     border: color-border-dim
│ ░  │                       │  ░ │     focus: border color-accent
│ ░  │ 説明（任意）           │  ░ │     height: 44px
│ ░  │ ┌───────────────────┐ │  ░ │
│ ░  │ │ 説明を入力...      │ │  ░ │  ← textarea: height 80px, resize: none
│ ░  │ │                   │ │  ░ │
│ ░  │ └───────────────────┘ │  ░ │
│ ░  │                       │  ░ │
│ ░  │ [キャンセル] [作成する] │  ░ │  ← btn row: gap-3, justify-end
│ ░  └───────────────────────┘  ░ │     キャンセル: text-secondary, no bg
│ ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░ │     作成する: gradient-play-btn, radius-btn-lg
└─────────────────────────────────┘
```

**バリデーション**:
- 名前: 必須、最大50文字。空の場合ボタンを`opacity-50 cursor-not-allowed`
- 説明: 任意、最大200文字
- 文字数カウンタ: input右下に `text-xs text-muted` で表示（例: `12/50`）

---

### 3.4 トラック追加モーダル

```
┌─────────────────────────────────┐
│ ░  ┌───────────────────────┐  ░ │
│ ░  │ トラックを追加    [×]  │  ░ │  ← modal: 同上、max-height: 80vh
│ ░  │                       │  ░ │
│ ░  │ 🔍 トラックを検索...   │  ░ │  ← search: bg-bg-deep, radius-chip
│ ░  │                       │  ░ │     icon: Search (lucide), left padding
│ ░  │ ─────────────────────  │  ░ │
│ ░  │                       │  ░ │
│ ░  │ ☑ トラックタイトル A   │  ░ │  ← track-row: height 52px
│ ░  │   Channel · 3:45      │  ░ │     checkbox: accent color
│ ░  │ □ トラックタイトル B   │  ░ │     選択済み: bg-bg-card-alt
│ ░  │   Channel · 4:12      │  ░ │
│ ░  │ □ トラックタイトル C   │  ░ │
│ ░  │   Channel · 2:58      │  ░ │
│ ░  │                       │  ░ │
│ ░  │ ─────────────────────  │  ░ │
│ ░  │ 2件選択中             │  ░ │  ← footer: 選択件数 + 追加ボタン
│ ░  │         [追加する]    │  ░ │     追加ボタン: 無効時 opacity-50
│ ░  └───────────────────────┘  ░ │
└─────────────────────────────────┘
```

**検索**: フロントエンド側でフィルタリング（既存 `getTracks()` APIから取得済みデータを絞り込み）
**スクロール**: トラックリスト部分のみスクロール（`overflow-y: auto`、`max-height: calc(80vh - 180px)`）

---

## 4. コンポーネント構成

### 新規コンポーネント

```
frontend/src/components/
├── PlaylistList.tsx          # プレイリスト一覧（タブコンテンツ）
├── PlaylistDetail.tsx        # プレイリスト詳細（フルスクリーン）
├── PlaylistCard.tsx          # プレイリスト一覧のカードアイテム
├── PlaylistTrackItem.tsx     # 詳細画面のトラック行（ドラッグ対応）
├── PlaylistCreateModal.tsx   # 作成/編集モーダル
└── TrackSelectModal.tsx      # トラック追加モーダル
```

### 変更する既存コンポーネント

| ファイル | 変更内容 |
|---------|---------|
| `TabBar.tsx` | `"playlist"` タブ追加（ListVideo アイコン、ラベル "PLAYLISTS"） |
| `App.tsx` | `activeTab` / `currentScreen` の型に `"playlist"` / `"playlist-detail"` 追加 |
| `MobileLayout.tsx` | `activeTab === "playlist"` 時に `<PlaylistList>` 表示; `currentScreen === "playlist-detail"` 時に `<PlaylistDetail>` 表示 |
| `TabletLayout.tsx` | 同上（サイドパネル or フルスクリーン対応） |
| `DesktopLayout.tsx` | プレイリスト詳細をサイドパネルとして表示 |

---

## 5. 画面遷移図

```
[ホーム: radioタブ]
        │
        ▼
[TABバー: PLAYLISTSタップ]
        │
        ▼
[プレイリスト一覧画面]
   │              │
   │[+]           │[カードタップ]
   ▼              ▼
[作成モーダル]  [プレイリスト詳細]
   │              │         │
[保存]           │[編集]   │[+ 追加]
   │              ▼         ▼
   └──────► [編集モーダル] [トラック追加モーダル]
                  │              │
                [保存]          [追加]
                  │              │
                  └──────────────┘
                         │
                [プレイリスト詳細（更新）]
                         │
              [▶ すべて再生 タップ]
                         │
                         ▼
              [ラジオ再生 → MiniPlayer表示]
```

---

## 6. 操作フロー詳細

### 6.1 プレイリスト作成フロー

1. PLAYLISTSタブ → `[+]` ボタンタップ
2. 作成モーダル表示（アニメーション: `translateY(100%) → translateY(0)`, `300ms ease-smooth`）
3. 名前入力（必須）、説明入力（任意）
4. `[作成する]` タップ → API `POST /api/playlists` → モーダル閉じる → リスト更新
5. 失敗時: モーダル内にエラーメッセージ（`text-sm color: #ef4444`）

### 6.2 トラック追加フロー

1. プレイリスト詳細 → `[+ 追加]` タップ
2. トラック追加モーダル表示
3. 検索 or スクロールでトラック選択（複数可）
4. `[追加する]` タップ → API `POST /api/playlists/:id/tracks` → モーダル閉じる → リスト更新
5. 重複トラックは選択不可（グレーアウト + "追加済み" バッジ）

### 6.3 ドラッグ&ドロップ並び替えフロー

1. トラック行の `≡`（GripVertical）をロングプレス or タッチ開始
2. アイテムが浮き上がるアニメーション（`shadow-float` + `scale(1.02)`）
3. ドラッグ中: 他アイテムが上下にスライド（`@dnd-kit/sortable` の `SortableContext`）
4. ドロップ → API `PATCH /api/playlists/:id/tracks/order` → UI即時反映

### 6.4 プレイリスト再生フロー

1. `[▶ すべて再生]` タップ → プレイリスト内トラックを順番にキューへ
2. MiniPlayerが表示（既存パターン流用）
3. `currentScreen` を `"nowplaying"` に変更して NowPlayingScreen表示

---

## 7. アクセシビリティ要件

| 要素 | 要件 |
|------|------|
| プレイリストカード | `role="button"`, `aria-label="[名前]を開く"` |
| 作成/編集モーダル | `role="dialog"`, `aria-modal="true"`, `aria-labelledby` |
| 削除ボタン | `aria-label="プレイリストを削除"` + 確認ダイアログ |
| チェックボックス | `aria-checked`, `aria-label="トラックを選択"` |
| ドラッグハンドル | `aria-label="並び替え"`, キーボード操作（矢印キー）対応 |

---

## 8. レスポンシブ対応

### モバイル（< 768px）：メイン対象
- タブコンテンツとして `PlaylistList` 表示
- 詳細はフルスクリーンオーバーレイ（`NowPlayingScreen` パターン踏襲）
- モーダルは画面下から `translateY` でスライドイン

### タブレット（768px - 1023px）
- タブコンテンツとして `PlaylistList` 表示
- 詳細はフルスクリーンオーバーレイ（2カラムレイアウト不要）
- モーダルはセンタリング（`translateY(0)` + `opacity` トランジション）

### デスクトップ（>= 1024px）
- プレイリスト詳細は右サイドパネル（既存の `showLyricsPanel` パターン流用）
- パネル幅: `360px`
- トラックリストは中央エリアに表示可能

---

## 9. アニメーション仕様

| 要素 | アニメーション |
|------|--------------|
| モーダル表示 | `opacity: 0→1` + `translateY(20px→0)`, `300ms var(--ease-smooth)` |
| モーダル非表示 | `opacity: 1→0` + `translateY(0→20px)`, `200ms var(--ease-out)` |
| プレイリスト詳細（モバイル） | `translateX(100%→0)`, `300ms var(--ease-smooth)` |
| カードホバー | `translateY(0→-2px)` + `shadow-float`, `150ms var(--duration-fast)` |
| ドラッグアイテム | `scale(1→1.02)` + `shadow-float`, `150ms var(--ease-bounce)` |
| リスト並び替え | `300ms var(--ease-smooth)` （@dnd-kit デフォルト） |
| プレイリスト作成後リスト更新 | `opacity: 0→1` + `translateY(10px→0)`, `300ms` staggered |

---

## 10. 状態管理の方針

- プレイリストデータは `App.tsx` でグローバル管理（`useState<Playlist[]>`）
- 詳細画面で選択中のプレイリストは `selectedPlaylistId: string | null`
- トラック追加の一時選択状態は `TrackSelectModal` ローカル state
- 楽観的UI更新（追加/削除は先にUIに反映し、API失敗時にロールバック）
