# SDD: UI刷新 Phase 1 — ビジュアル強化

| 項目 | 内容 |
|------|------|
| Issue | #347 UI刷新: AI Music Station モダンデザイン化 |
| Phase | 1 — ビジュアル強化 |
| 作成日 | 2026-03-22 |
| 作成者 | Director / Designer |

---

## 1. 概要

### 1.1 目的
AI Music Station のUIをモダンデザインに刷新する。Phase 1 ではビジュアル面の強化に焦点を当て、チャンネル選択のカード型レイアウト化、プレーヤーの視覚強化、マイクロインタラクション追加、ネオモーフィズム要素の導入を行う。

### 1.2 スコープ
1. **チャンネル選択のカード型レイアウト** — ボタン型 → カード型、アイコン・メタデータ表示
2. **プレーヤーの視覚強化** — プログレスリング、再生状態フィードバック
3. **マイクロインタラクション** — ホバー・タップ・状態遷移アニメーション
4. **ネオモーフィズム要素** — soft shadow / inset 効果

### 1.3 技術制約
- React 19 + TypeScript + Vite + Tailwind 4
- **新規ライブラリ追加禁止**（CSS + 既存CSS変数のみ）
- 既存デザイントークン（CSS Custom Properties）を活用・拡張

---

## 2. 仕様策定（Director）

> **作成者**: Director
> **調査日**: 2026-03-22
> **調査対象**: `frontend/src/` 全コンポーネント・Issue #347

### 2.1 現状分析（As-Is）

コードベース調査により、以下の現状を確認した。

#### ChannelSelector（`ChannelSelector.tsx`）

| 項目 | 現状 |
|------|------|
| レイアウト | `flex gap-3 flex-wrap` — フラットなボタン行 |
| 表示情報 | チャンネル名 + キュー深度（`queue_depth`）のみ |
| アイコン | なし |
| `total_tracks` | 未表示（APIレスポンスに存在するが未使用） |
| アクティブ状態 | グラデーションクラス切り替え + `scale-105` |

#### Player（`Player.tsx`）

| 項目 | 現状 |
|------|------|
| 再生ボタン | 64×64px 円形（`w-16 h-16`）、グラデーション背景 |
| プログレス表示 | shimmerアニメーションのみ（実際の進捗は非反映） |
| `elapsedMs`/`durationMs` | propsなし（`App.tsx`には`elapsedMs`状態あり、未接続） |
| ビジュアライザー | 5本バーのアニメーション（再生中のみ表示） |

#### NowPlaying（`NowPlaying.tsx`）

| 項目 | 現状 |
|------|------|
| 背景グラデーション | 固定（indigo/purple/pink）— チャンネル非連動 |
| 再生中インジケーター | `animate-pulse` の緑ドット |
| メタデータバッジ | `bg-white/5` フラット（ネオモーフィズムなし） |
| 入場アニメーション | staggerなし |

#### TrackHistory（`TrackHistory.tsx`）

| 項目 | 現状 |
|------|------|
| ホバーエフェクト | `glass-card-hover` クラスのみ（アクセントラインなし） |
| 歌詞展開 | 条件付きレンダリング（`{isExpanded && ...}`）— トランジションなし |
| リスト入場 | アニメーションなし |

#### App.tsx

- `elapsedMs` 状態を保有するが `Player` に渡していない
- `durationMs` は `nowPlaying.duration_ms` から取得可能
- `max-w-2xl` の単一カラム構成（2カラム化が必要）

#### LyricsDisplay（`LyricsDisplay.tsx`）

- 既存: 現在行のみハイライト表示、全文スクロールモードなし
- `elapsedMs` / `durationMs` は受け取っているが全文表示に未対応

#### AudioVisualizer

- 未存在。新規作成が必要

#### バックエンド: `worker/playlist_generator.py`

- **既知バグ**: トラックファイルパスをホスト側パス（`generated_tracks/`）で生成している
- Liquidsoap コンテナは `/tracks/` マウントでファイルを参照するため、プレイリストがマッチしない
- 影響: えぐしゅぎチャンネルなど一部チャンネルでストリーミング再生が機能しない

---

### 2.2 機能要件（Functional Requirements）

#### FR-101: チャンネルカード型表示

| ID | 要件 | 優先度 |
|----|------|--------|
| FR-101-1 | ChannelSelector をグリッドレイアウトのカード型に変更する | Must |
| FR-101-2 | 各カードにチャンネル固有の絵文字アイコンを表示する | Must |
| FR-101-3 | 各カードにチャンネル名を表示する | Must |
| FR-101-4 | 各カードに `total_tracks`（曲数）を表示する | Must |
| FR-101-5 | `queue_depth > 0` の場合、待ちキュー数を表示する | Should |
| FR-101-6 | アクティブカードにインジケータードット（`glow-pulse`）を表示する | Must |
| FR-101-7 | ホバー時に `translateY(-4px)` のリフトアップを行う | Should |
| FR-101-8 | タップ時に `scale(0.97)` のプレスフィードバックを行う | Should |

#### FR-102: プレーヤー視覚強化

| ID | 要件 | 優先度 |
|----|------|--------|
| FR-102-1 | 再生ボタンをSVGプログレスリング（72px）で囲む | Must |
| FR-102-2 | `elapsedMs` / `durationMs` を Player に渡し、リングの進捗に反映する | Must |
| FR-102-3 | `App.tsx` から `Player` へ `elapsedMs` / `durationMs` propsを追加する | Must |
| FR-102-4 | 再生ボタンにネオモーフィズムシャドウを適用する | Should |
| FR-102-5 | 既存の線形プログレスバーに実際の進捗（`elapsedMs / durationMs`）を反映する | Must |

#### FR-103: NowPlaying 視覚強化

| ID | 要件 | 優先度 |
|----|------|--------|
| FR-103-1 | 背景グラデーションをチャンネルスラグに連動して動的切り替えする | Must |
| FR-103-2 | 再生中インジケーターを `glow-pulse` クラスに変更する | Should |
| FR-103-3 | メタデータバッジに `badge-neo` クラス（ネオモーフィズム inset shadow）を適用する | Should |
| FR-103-4 | メタデータバッジに stagger 付き入場アニメーションを追加する | Should |

#### FR-104: TrackHistory マイクロインタラクション

| ID | 要件 | 優先度 |
|----|------|--------|
| FR-104-1 | ホバー時に左端にチャンネルカラーのアクセントライン（3px）を表示する | Should |
| FR-104-2 | 歌詞展開を条件付きレンダリングから常時レンダリング＋CSS `max-height` トランジションに変更する | Must |
| FR-104-3 | リストアイテムに stagger 付き入場アニメーションを追加する | Should |

#### FR-105: RequestForm 視覚強化

| ID | 要件 | 優先度 |
|----|------|--------|
| FR-105-1 | 入力フィールドのフォーカス時にネオモーフィズム inset shadow を適用する | Should |
| FR-105-2 | 送信ボタンに hover/active ネオモーフィズムエフェクトを適用する | Should |
| FR-105-3 | 成功/エラーメッセージに `slide-up` 入場アニメーションを追加する | Should |

#### FR-106: オーディオビジュアライザー（新規）

Web Audio API + Canvas を用いたリアルタイム周波数ビジュアライザーを右カラムに追加する。

| ID | 要件 | 優先度 |
|----|------|--------|
| FR-106-1 | Web Audio API（`AudioContext`, `AnalyserNode`）でストリーム音声の周波数データを取得する | Must |
| FR-106-2 | Canvas 2D コンテキストで周波数スペクトルをバー表示する（Windows Media Player / iTunes 風） | Must |
| FR-106-3 | バーの色をチャンネルグラデーションに連動させる | Should |
| FR-106-4 | 再生停止時はアニメーションを停止し、Canvas をクリアする | Must |
| FR-106-5 | `prefers-reduced-motion` 時はビジュアライザーを非表示にする | Must |
| FR-106-6 | Safari の `webkitAudioContext` フォールバックに対応する | Must |
| FR-106-7 | 新規コンポーネント `AudioVisualizer.tsx` として実装する | Must |

#### FR-107: 2カラムレイアウト（新規）

| ID | 要件 | 優先度 |
|----|------|--------|
| FR-107-1 | デスクトップ（≥ 1024px）で左右2カラムレイアウトに変更する | Must |
| FR-107-2 | 左カラム: チャンネル選択 + Player + リクエストフォーム + トラック一覧 | Must |
| FR-107-3 | 右カラム: `MediaDisplay`（ビジュアライザーを全面背景表示し、その上に歌詞テキストをオーバーレイ） | Must |
| FR-107-4 | タブレット（768〜1023px）では左カラム320px固定の2カラム表示、モバイル（< 768px）では1カラムに縦積みし、`MediaDisplay`を下部に表示する | Must |
| FR-107-5 | `App.tsx` のレイアウトコンテナを `max-w-2xl` → `max-w-6xl` に拡張する | Must |

**右カラムのレイヤー構成（カラオケ映像方式）**:
```
┌───────────────────────────────────┐
│  [AudioVisualizer]                 │  ← 背景層: Canvas 全面表示
│                                    │     (position: relative, 100% width/height)
│  ┌────────────────────────────┐   │
│  │  過去行: opacity-40        │   │  ← 前景層: 歌詞オーバーレイ
│  │  ▶ 現在行: font-bold ◀    │   │     (position: absolute, inset-0, z-10)
│  │  未来行: 通常色            │   │     背景: gradient fade (上下)
│  └────────────────────────────┘   │
└───────────────────────────────────┘
歌詞なし → ビジュアライザーのみ表示（オーバーレイ非表示）
```

**実装方針（CSS）**:
```css
.media-display {
  position: relative;
  width: 100%;
  aspect-ratio: 16 / 9;  /* または min-height: 400px */
}

.lyrics-overlay {
  position: absolute;
  inset: 0;
  z-index: 10;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  /* 上下にグラデーションフェード */
  mask-image: linear-gradient(to bottom, transparent 0%, black 15%, black 85%, transparent 100%);
  -webkit-mask-image: linear-gradient(to bottom, transparent 0%, black 15%, black 85%, transparent 100%);
}
```

#### FR-108: Player 曲名表示改善（新規）

| ID | 要件 | 優先度 |
|----|------|--------|
| FR-108-1 | Player に現在再生中の曲名を大きく（`text-xl font-bold` 以上）表示する | Must |
| FR-108-2 | `nowPlaying` がない場合は「チャンネルを選択して再生を開始してください」と表示する（「再生中のトラックはありません」を廃止） | Must |
| FR-108-3 | 曲名が長い場合はマーキー（横スクロール）アニメーションを適用する | Should |
| FR-108-4 | `nowPlaying.title` を優先し、なければ `nowPlaying.caption` を表示する（既存ロジック継承） | Must |

#### FR-109: 歌詞カラオケ表示 — ビジュアライザーオーバーレイ（新規）

歌詞をビジュアライザーの**上にオーバーレイ表示**する。カラオケ映像と同じ構成：背景=ビジュアライザー、前景=歌詞テキスト。

| ID | 要件 | 優先度 |
|----|------|--------|
| FR-109-1 | 歌詞がある場合、`MediaDisplay` 内のビジュアライザー上に `position: absolute` でオーバーレイ表示する | Must |
| FR-109-2 | 既存の `LyricsDisplay` コンポーネントを拡張し、`mode="karaoke-overlay"` prop でオーバーレイモードを切り替え可能にする | Must |
| FR-109-3 | `elapsedMs` に基づき現在行を強調表示（`text-accent` + `scale-105` + `font-bold`）する | Must |
| FR-109-4 | 過去行を薄く表示（`opacity-40`）、未来行を通常色で表示する | Must |
| FR-109-5 | **タイミング推定（Phase 1）**: `Math.floor(elapsedMs / (durationMs / lyrics.length))` で現在行インデックスを算出する | Must |
| FR-109-6 | ハイライト行が常にオーバーレイエリアの中央付近に位置するよう `scrollIntoView({ behavior: 'smooth', block: 'center' })` で追従する | Must |
| FR-109-7 | 歌詞なしの場合はオーバーレイを非表示にし、ビジュアライザーのみ表示する | Must |
| FR-109-8 | オーバーレイエリアは `inset-0` + `overflow: hidden`、上下にグラデーションフェード（mask-image）を適用する | Must |
| FR-109-9 | テキストにドロップシャドウ（`text-shadow`）を付け、ビジュアライザー上での可読性を確保する | Must |
| FR-109-10 | **将来フェーズ（Phase 2）**: タイムスタンプ付き歌詞データ（LRC形式等）に対応する（Phase 1では不要） | Won't |

**タイミング推定ロジック（Phase 1）**:
```ts
// 楽曲長 ÷ 歌詞行数で均等分割
const linesArray = lyrics.trim().split("\n").filter(Boolean);
const currentIndex = durationMs > 0
  ? Math.min(
      Math.floor(elapsedMs / (durationMs / linesArray.length)),
      linesArray.length - 1
    )
  : 0;
```

**行ごとのスタイル**:
| 状態 | スタイル |
|------|---------|
| 過去行 | `opacity-40` |
| 現在行 | `font-bold text-accent scale-105`（ハイライト） |
| 未来行 | デフォルト（`opacity-100`） |

#### FR-111: MediaDisplay ラッパーコンポーネント（拡張性設計）

将来的に Music Video 表示とビジュアライザーを切り替え可能にするための **MediaDisplay** ラッパーを Phase 1 で設計・実装する。

| ID | 要件 | 優先度 | フェーズ |
|----|------|--------|---------|
| FR-111-1 | `MediaDisplay` コンポーネントを新規作成し、右カラムのメインエリアとして配置する | Must | Phase 1 |
| FR-111-2 | Phase 1 では `AudioVisualizer`（背景）+ 歌詞オーバーレイ（前景）の2層構成で実装する | Must | Phase 1 |
| FR-111-3 | Phase 2 では `nowPlaying.video_url` が存在する場合に `<video>` タグを背景層に使用し、歌詞オーバーレイはそのまま維持する | N/A | Phase 2 |
| FR-111-4 | コンポーネントインターフェース（Section 3.4定義に準拠）: `<MediaDisplay audioRef={audioRef} isPlaying={isPlaying} channelSlug={channelSlug} videoUrl={nowPlaying?.video_url} lyrics={nowPlaying?.lyrics} elapsedMs={elapsedMs} durationMs={nowPlaying?.duration_ms ?? 0} />` | Must | Phase 1 |
| FR-111-5 | 歌詞がある場合は `LyricsDisplay mode="karaoke-overlay"` を前景層として内包する | Must | Phase 1 |
| FR-111-6 | 歌詞がない場合は前景層を非表示にし、ビジュアライザーのみ表示する | Must | Phase 1 |

**コンポーネント構造（Phase 1）**:
```tsx
function MediaDisplay({ nowPlaying, isPlaying, channelSlug, elapsedMs }: MediaDisplayProps) {
  return (
    <div className="media-display relative w-full" style={{ aspectRatio: '16/9' }}>
      {/* 背景層: AudioVisualizer (Phase 2では video_url があれば VideoPlayer に差し替え) */}
      {/* Phase 2 拡張ポイント: if (nowPlaying?.video_url) → <VideoPlayer> */}
      <AudioVisualizer isPlaying={isPlaying} channelSlug={channelSlug} />

      {/* 前景層: 歌詞オーバーレイ (歌詞なしは非表示) */}
      {nowPlaying?.lyrics && (
        <LyricsDisplay
          lyrics={nowPlaying.lyrics}
          elapsedMs={elapsedMs}
          durationMs={nowPlaying.duration_ms ?? 0}
          mode="karaoke-overlay"
        />
      )}
    </div>
  );
}
```

**拡張ロードマップ**:
| フェーズ | 背景層 | 前景層（歌詞） |
|---------|--------|--------------|
| Phase 1 | AudioVisualizer | karaoke-overlay（推定タイミング） |
| Phase 2 | video_url あり → VideoPlayer / なし → AudioVisualizer | karaoke-overlay（LRCタイムスタンプ対応） |

---

#### FR-110: バグ修正 — えぐしゅぎチャンネル ストリーミングパス（新規）

| ID | 要件 | 優先度 |
|----|------|--------|
| FR-110-1 | `worker/playlist_generator.py` のトラックパス生成を修正する | Must |
| FR-110-2 | ホスト側パス（`generated_tracks/`）ではなく Liquidsoap コンテナ内パス（`/tracks/`）を出力するよう修正する | Must |
| FR-110-3 | 修正後、えぐしゅぎチャンネルを含む全チャンネルでストリーミングが正常に機能することを確認する | Must |

---

### 2.3 非機能要件（Non-Functional Requirements）

#### NFR-201: パフォーマンス

| ID | 要件 | 基準値 |
|----|------|--------|
| NFR-201-1 | アニメーションは GPU合成プロパティのみ使用（`transform`, `opacity`）。`transition: all` 禁止、明示的プロパティ列挙必須 | 必須 |
| NFR-201-2 | `box-shadow`, `transform`, `border-color`, `background-color` のみ `transition` 対象とし、layout shiftを防止する | 必須 |
| NFR-201-2a | **例外**: 歌詞展開の `max-height` トランジション（FR-104）はアニメーションのため許可。ただし固定値（`max-height: 500px`）を指定し、`auto` への直接トランジションは不可 | 例外 |
| NFR-201-3 | `ProgressRing` の不要な再レンダリングを防止する（`React.memo` 検討） | 推奨 |
| NFR-201-4 | Lighthouse Performance スコア 85以上を維持する | 目標 |

#### NFR-202: アクセシビリティ

| ID | 要件 | 基準値 |
|----|------|--------|
| NFR-202-1 | テキスト（primary）のコントラスト比 4.5:1 以上（WCAG AA） | 必須 |
| NFR-202-2 | Tab キーで全インタラクティブ要素にフォーカスが到達すること | 必須 |
| NFR-202-3 | `prefers-reduced-motion` 時に全アニメーションを無効化すること | 必須 |
| NFR-202-4 | チャンネルカードに適切な `aria-label` / `aria-pressed` を付与すること | 必須 |
| NFR-202-5 | 操作要素に `touch-action: manipulation` を付与すること | 推奨 |

#### NFR-203: ブラウザ互換性

| ID | 要件 | 対象 |
|----|------|------|
| NFR-203-1 | Chrome latest / Safari latest / Firefox latest で動作すること | 必須 |
| NFR-203-2 | `backdrop-filter` は Safari prefix（`-webkit-backdrop-filter`）を付与すること | 必須 |
| NFR-203-3 | ネオモーフィズムシャドウの各ブラウザ描画を確認すること | 必須 |

#### NFR-204: 技術制約

| ID | 要件 |
|----|------|
| NFR-204-1 | 新規 **npm パッケージ** 追加禁止（CSS + 既存CSS変数・Tailwind 4 のみ）。ただし **ブラウザ標準 Web API**（Web Audio API, Canvas API）は利用可 |
| NFR-204-2 | React 19 + TypeScript + Vite + Tailwind 4 の既存スタックを維持すること |
| NFR-204-3 | `npm run build` が警告なしで成功すること |
| NFR-204-4 | TypeScript 型エラーがないこと |
| NFR-204-5 | ビジュアライザーは Canvas 2D API で実装する（WebGL は将来対応、Phase 1では不要） |

#### NFR-206: ビジュアライザーパフォーマンス

| ID | 要件 | 基準値 |
|----|------|--------|
| NFR-206-1 | `requestAnimationFrame` ループを使用し、不要な描画を防ぐ | 必須 |
| NFR-206-2 | コンポーネントアンマウント時に `AudioContext.close()` と `cancelAnimationFrame()` を呼ぶ | 必須 |
| NFR-206-3 | ビジュアライザー動作中もページのメインスレッドがブロックされないこと | 必須 |

#### NFR-205: レスポンシブ

| ID | 要件 | ブレークポイント |
|----|------|----------------|
| NFR-205-1 | 320px / 480px / 640px / 768px / 1024px でレイアウト崩れがないこと | 全幅 |
| NFR-205-2 | チャンネルカードのグリッド列数が画面幅に応じて正しく切り替わること | 320px / 480px / 640px+ |
| NFR-205-3 | モバイル（< 640px）でPlayerが縦積みレイアウトになること | < 640px |

---

### 2.4 スコープ定義

#### In Scope（Phase 1 対象）

| # | 対象 | FR参照 |
|---|------|--------|
| 1 | ChannelSelector: ボタン型 → カード型グリッドへの全面書き換え | FR-101 |
| 2 | Player: SVGプログレスリング、ネオモーフィズム、曲名大表示、実進捗バー | FR-102, FR-108 |
| 3 | NowPlaying: チャンネル連動グラデーション、stagger入場、ネオモーフィズムバッジ | FR-103 |
| 4 | TrackHistory: アクセントライン、歌詞展開アニメーション | FR-104 |
| 5 | RequestForm: フォーカス・ボタン・メッセージアニメーション強化 | FR-105 |
| 6 | **AudioVisualizer（新規）**: Web Audio API + Canvas、右カラム配置 | FR-106 |
| 7 | **2カラムレイアウト（新規）**: デスクトップ2列・モバイル1列 | FR-107 |
| 8 | **歌詞全文スクロール（新規）**: カラオケ風、再生位置追従 | FR-109 |
| 9 | **バグ修正（新規）**: `playlist_generator.py` Liquidsoapパス修正 | FR-110 |
| 10 | App.tsx: レイアウト拡張（`max-w-6xl`）、props接続 | FR-107, FR-102 |
| 11 | styles.css: デザイントークン拡張、新CSSクラス・@keyframes追加 | — |

#### Out of Scope（Phase 1 対象外）

| # | 対象外 | 理由 |
|---|--------|------|
| 1 | 多言語対応（i18n） | 現時点で日本語のみ（CLAUDE.md方針） |
| 2 | PWA化・オフライン対応 | Phase 2以降で検討 |
| 3 | 新規 npm パッケージ導入 | 技術制約 NFR-204-1（ブラウザ標準APIは可） |
| 4 | ダークモード/ライトモード切り替え | 現状ダークモード固定 |
| 5 | WebGL ビジュアライザー | Phase 1 は Canvas 2D で実装。WebGL は Phase 2 で検討 |
| 6 | バックエンドAPI 新規エンドポイント追加 | 既存エンドポイントの範囲内で実装 |

---

### 2.5 修正対象ファイル一覧（Director 確認版）

#### フロントエンド

| ファイル | 変更種別 | 変更内容概要 | FR参照 |
|---------|---------|------------|--------|
| `frontend/src/styles.css` | 追記 | デザイントークン追加、新CSSクラス・@keyframes追加 | 全般 |
| `frontend/src/App.tsx` | 修正 | 2カラムレイアウト化（`max-w-6xl`）、props接続、AudioVisualizer組込 | FR-107 |
| `frontend/src/components/ChannelSelector.tsx` | 全面書き換え | カード型グリッドレイアウト、アイコン・曲数表示 | FR-101 |
| `frontend/src/components/Player.tsx` | 機能追加 | ProgressRing、ネオモーフィズム、曲名大表示、props追加（`elapsedMs`/`durationMs`）、`audioRef` を `MediaDisplay` へ受け渡し（Web Audio API 接続用） | FR-102, FR-108 |
| `frontend/src/components/NowPlaying.tsx` | 機能追加 | 動的グラデーション、stagger入場、バッジ強化 | FR-103 |
| `frontend/src/components/TrackHistory.tsx` | 機能追加 | アクセントライン、歌詞展開CSSトランジション | FR-104 |
| `frontend/src/components/RequestForm.tsx` | 機能追加 | フォーカス・ボタン・メッセージアニメーション | FR-105 |
| `frontend/src/components/AudioVisualizer.tsx` | **新規作成** | Web Audio API + Canvas 2D ビジュアライザー | FR-106 |
| `frontend/src/components/MediaDisplay.tsx` | **新規作成** | AudioVisualizer/VideoPlayer 切替ラッパー（Phase 1はVisualizer固定） | FR-111 |
| `frontend/src/components/LyricsDisplay.tsx` | 機能追加 | カラオケオーバーレイモード追加（`mode="karaoke-overlay"` prop）、`scrollIntoView` 自動追従 | FR-109 |

#### バックエンド

| ファイル | 変更種別 | 変更内容概要 | FR参照 |
|---------|---------|------------|--------|
| `worker/playlist_generator.py` | バグ修正 | トラックパス生成を `generated_tracks/` → `/tracks/` に修正 | FR-110 |

---

### 2.6 受け入れ基準（Acceptance Criteria）

| # | 観点 | 基準 | FR参照 |
|---|------|------|--------|
| AC-01 | ChannelSelector | アクティブチャンネルのカードが `channel-gradient-*` グラデーションで強調表示される | FR-101 |
| AC-02 | Player — ProgressRing | 再生中、SVGプログレスリングが `elapsedMs / durationMs` に基づき進捗を表示する | FR-102 |
| AC-03 | Player — 曲名 | 再生中の曲名が Player に大きく表示される（`text-xl` 以上）。未選択時は適切なプレースホルダーを表示 | FR-108 |
| AC-04 | NowPlaying | チャンネル切り替え時に背景グラデーションが変化する | FR-103 |
| AC-05 | TrackHistory | 歌詞展開クリック時にアニメーション付きで展開・折りたたまれる | FR-104 |
| AC-06 | RequestForm | 入力フォーカス時にネオモーフィズムフォーカスリングが表示される | FR-105 |
| AC-07 | AudioVisualizer | 再生中、音声に連動したビジュアライザーバーが右カラムに表示される | FR-106 |
| AC-08 | AudioVisualizer | 停止時はビジュアライザーが停止・クリアされる | FR-106 |
| AC-09 | 2カラムレイアウト | デスクトップ（≥1024px）で左右2カラム表示される | FR-107 |
| AC-10 | 2カラムレイアウト | モバイル（< 768px）で1カラムに縦積みされる | FR-107 |
| AC-11 | 歌詞カラオケオーバーレイ | ビジュアライザーの上に歌詞がオーバーレイ表示され、再生に追従して現在行がハイライトされる。歌詞なし曲はオーバーレイ非表示 | FR-109 |
| AC-12 | バグ修正 | えぐしゅぎチャンネル含む全チャンネルでストリーミングが途切れずに再生される | FR-110 |
| AC-13 | レスポンシブ | 320px〜1440px で全コンポーネントが正常表示される | NFR-205 |
| AC-14 | アクセシビリティ | `prefers-reduced-motion` でアニメーション・ビジュアライザーが無効になる | NFR-202 |
| AC-15 | ビルド | `npm run build` が警告・エラーなしで完了する | NFR-204 |

---

## 3. UI/UX設計（Designer）

> **作成者**: Designer
> **作成日**: 2026-03-22（tto要望・追加指示に基づき全面改訂 v3）
> **主要変更**:
> - 2カラムレイアウト（左: 操作パネル / 右: メディア全面）
> - MediaDisplay ラッパー（AudioVisualizer / 将来Music Video 切り替え）
> - LyricsDisplay mode="karaoke-overlay"（ビジュアライザー上に歌詞オーバーレイ）
> - 曲名大表示 / モバイル対応詳細設計

### 3.1 情報アーキテクチャ

```
アプリ起動
  └─ チャンネル一覧ロード（useChannels）
       └─ チャンネル選択（ChannelSelector）← 左カラム
            ├─ ストリーム再生開始（Player）← 左カラム
            │    ├─ MediaDisplay 起動（右カラム全面）
            │    │    ├─ videoUrl あり → <video> Music Video 再生
            │    │    └─ videoUrl なし → AudioVisualizer（Web Audio API + Canvas）
            │    ├─ LyricsDisplay（mode="karaoke-overlay"）表示（MediaDisplay 上にオーバーレイ）
            │    └─ 再生中に音量調整・再生/停止
            ├─ 再生中曲名の大表示（Player内・曲名強調）← 左カラム
            ├─ トラック履歴（TrackHistory）← 左カラム下部
            └─ 楽曲リクエスト（RequestForm）← 左カラム中部
                 └─ 送信 → 待ち順確認
```

### 3.2 アプリケーション全体ワイヤーフレーム

#### デスクトップ（≥ 1024px）: 2カラムレイアウト

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         AI Music Station                                │  ← ヘッダー
│                    AIが生成した音楽をライブ配信                              │
│                         ⚙️ チャンネル管理                                 │
├──────────────────────────────────┬──────────────────────────────────────┤
│  左カラム（flex: 0 0 400px）        │  右カラム（flex: 1）                  │
│                                  │                                      │
│  ┌──────────────────────────┐   │  ┌──────────────────────────────┐   │
│  │  🎧   🎤   🎷   🎮      │   │  │                              │   │
│  │  Lo-Fi Anime Jazz Game  │   │  │   [MediaDisplay]             │   │
│  └──────────────────────────┘   │  │                              │   │
│  ← ChannelSelector               │  │   ████ AudioVisualizer ████  │   │
│                                  │  │   ████ (Canvas 2D)     ████  │   │
│  ┌──────────────────────────┐   │  │   ████ バーグラフ+ミラー ████  │   │
│  │ ╭──────╮                 │   │  │                              │   │
│  │╱ SVGリング╲               │   │  │  ┄┄┄┄┄┄┄ オーバーレイ ┄┄┄┄┄┄  │   │
│  ││ [▶/❚❚] │  ◆曲名（大）◆ │   │  │  (z-index: 10)               │   │
│  │╲        ╱  チャンネル名  │   │  │  ♪ 過去行（opacity 0.25）    │   │
│  │ ╰──────╯  🔊──────────  │   │  │  ♪ 過去行（opacity 0.4）     │   │
│  │ ■■■■■□□□□ プログレスバー │   │  │► ♪ 現在のライン（ハイライト）◄  │   │
│  └──────────────────────────┘   │  │  ♪ 未来行（通常色）          │   │
│  ← Player（曲名text-2xl強調）     │  │  ♪ 未来行（通常色）          │   │
│                                  │  │  ┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄  │   │
│  ┌──────────────────────────┐   │  │                              │   │
│  │ ● 再生中  [👍] [❤️]      │   │  └──────────────────────────────┘   │
│  │ [120 BPM] [Cm] [210秒]  │   │  ← MediaDisplay（全面 + 歌詞オーバーレイ）│
│  └──────────────────────────┘   │                                      │
│  ← NowPlaying（メタデータ）        │                                      │
│                                  │                                      │
│  ┌──────────────────────────┐   │                                      │
│  │ トラックをリクエスト         │   │                                      │
│  │ [BPM]  [リクエスト送信]    │   │                                      │
│  └──────────────────────────┘   │                                      │
│  ← RequestForm                   │                                      │
│                                  │                                      │
│  ┌──────────────────────────┐   │                                      │
│  │ 最近のトラック              │   │                                      │
│  │ ▶ トラック名A   5回再生   │   │                                      │
│  └──────────────────────────┘   │                                      │
│  ← TrackHistory                  │                                      │
├──────────────────────────────────┴──────────────────────────────────────┤
│                  AI Music Station — ACE-Step v1.5 搭載                   │
└─────────────────────────────────────────────────────────────────────────┘
```

#### MediaDisplay の内部レイヤー構造

```
┌─────────────────────────────────┐
│  MediaDisplay（position: relative）│
│                                  │
│  ┌───────────────────────────┐  │  z-index: 0
│  │  AudioVisualizer          │  │  ← または <video> (videoUrl あり時)
│  │  Canvas 全面描画           │  │
│  └───────────────────────────┘  │
│                                  │
│  ┌───────────────────────────┐  │  z-index: 10
│  │  LyricsDisplay            │  │  ← position: absolute, inset: 0
│  │  (position: absolute)     │  │    歌詞なし時は非表示
│  │                           │  │
│  │   ♪ 過去行（dim）          │  │
│  │   ♪ 過去行（dim）          │  │
│  │ ► ♪ 現在行（highlight）  ◄ │  │
│  │   ♪ 未来行                │  │
│  │   ♪ 未来行                │  │
│  └───────────────────────────┘  │
│                                  │
└─────────────────────────────────┘
```

#### モバイル（< 768px）: シングルカラム

```
┌──────────────────────────────────────────┐
│           AI Music Station               │
├──────────────────────────────────────────┤
│  ChannelSelector（カードグリッド 2-3列）   │
├──────────────────────────────────────────┤
│  Player（ProgressRing + 曲名大表示）        │
│  [▶/❚❚]  ◆ トラック名 ◆  🔊            │
├──────────────────────────────────────────┤
│  MediaDisplay（高さ: 240px）              │  ← ビジュアライザー + 歌詞オーバーレイ
│  ████ AudioVisualizer ████               │
│    ♪ 過去行（dim）                        │  オーバーレイ表示
│  ► ♪ 現在行（highlight）                  │
│    ♪ 未来行                              │
├──────────────────────────────────────────┤
│  NowPlaying（メタデータ）                  │
├──────────────────────────────────────────┤
│  RequestForm                             │
├──────────────────────────────────────────┤
│  TrackHistory                            │
└──────────────────────────────────────────┘
```

### 3.3 コンポーネント階層

```
App
├── <div class="app-layout">              ← 2カラムグリッド / 1カラム（モバイル）
│   │
│   ├── <aside class="left-column">
│   │   ├── ChannelSelector
│   │   │   └── <button class="channel-card" role="radio" aria-checked> × N
│   │   │       ├── <div class="channel-card-icon">（emoji 円形）
│   │   │       ├── <div class="channel-card-name">
│   │   │       ├── <div class="channel-card-meta">（曲数 · 待ち件数）
│   │   │       └── <span class="channel-card-active-dot">
│   │   │
│   │   ├── Player
│   │   │   ├── <audio> ref
│   │   │   ├── <div class="player-controls">
│   │   │   │   ├── ProgressRing（SVGコンポーネント）
│   │   │   │   └── <button class="player-button" aria-label>
│   │   │   ├── <div class="player-track-info">      ← 新規
│   │   │   │   ├── <div class="now-playing-title">  ← 曲名大表示（clamp font-size）
│   │   │   │   └── <div class="now-playing-channel">
│   │   │   ├── VolumeControl
│   │   │   └── <div class="progress-bar">（実進捗 width）
│   │   │
│   │   ├── NowPlaying
│   │   │   ├── <div> 背景グラデーション（channel-gradient-* 動的）
│   │   │   ├── <span class="glow-pulse">
│   │   │   ├── <div class="stagger-fade-in">
│   │   │   │   └── <span class="badge-neo"> × N
│   │   │   └── ReactionButton
│   │   │
│   │   ├── RequestForm
│   │   │   └── （既存フィールド + btn-submit）
│   │   │
│   │   └── TrackHistory
│   │       └── <div class="track-item"> × N
│   │
│   └── <main class="right-column">
│       └── MediaDisplay（新規ラッパーコンポーネント）← 右カラム全面
│           ├── Props: { audioRef, isPlaying, channelSlug, videoUrl? }
│           ├── videoUrl あり時:
│           │   └── <video class="media-video" src={videoUrl} autoPlay loop muted />
│           └── videoUrl なし時:
│               └── AudioVisualizer
│                   └── <canvas class="viz-canvas">
│           │
│           └── LyricsDisplay mode="karaoke-overlay"（lyrics あり時のみ表示）
│               ├── position: absolute, inset: 0, z-index: 10
│               ├── Props: { lyrics, elapsedMs, durationMs, mode="karaoke-overlay" }
│               └── <div class="karaoke-scroll-container">
│                   └── <div class="karaoke-line [past|active|future]"> × N
│                       ├── 過去行: opacity 0.25 → 0.4（直前行）
│                       ├── アクティブ行: チャンネルカラーグラデーション + glow
│                       └── 未来行: var(--text-primary) 通常色
```

### 3.4 MediaDisplayコンポーネント仕様（新規ラッパー）

#### 概要

右カラム全面を占めるメディア表示ラッパー。Phase 1 では `videoUrl` が未設定なので AudioVisualizer を表示。将来フェーズで `videoUrl` が渡されると Music Video を再生する。LyricsDisplay（mode="karaoke-overlay"）は常に子として配置し、歌詞の有無で表示切り替え。

#### コンポーネントインターフェース

```tsx
interface MediaDisplayProps {
  audioRef: React.RefObject<HTMLAudioElement>;  // AudioVisualizer 用
  isPlaying: boolean;
  channelSlug: string | null;
  videoUrl?: string;                            // 将来Music Video対応
  // LyricsDisplay karaoke-overlay用
  lyrics?: string | null;
  elapsedMs: number;
  durationMs: number;
}
```

#### 表示ロジック

```tsx
function MediaDisplay({ videoUrl, audioRef, isPlaying, channelSlug,
                        lyrics, elapsedMs, durationMs }: MediaDisplayProps) {
  return (
    <div className="media-display">
      {/* 背景レイヤー（z-index: 0） */}
      {videoUrl ? (
        <video className="media-video" src={videoUrl} autoPlay loop muted playsInline />
      ) : (
        <AudioVisualizer audioRef={audioRef} isPlaying={isPlaying} channelSlug={channelSlug} />
      )}

      {/* 前景レイヤー — 歌詞オーバーレイ（z-index: 10） */}
      {lyrics && (
        <LyricsDisplay
          mode="karaoke-overlay"
          lyrics={lyrics}
          elapsedMs={elapsedMs}
          durationMs={durationMs}
          channelSlug={channelSlug}
        />
      )}
    </div>
  );
}
```

#### CSS

```css
.media-display {
  position: relative;
  width: 100%;
  height: var(--viz-height);       /* デスクトップ: 100%高さ / モバイル: 240px */
  border-radius: 1rem;
  overflow: hidden;
  border: 1px solid var(--border-glass);
  box-shadow: var(--neo-shadow-out);
  background: var(--bg-secondary);
}

.media-video {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
  z-index: 0;
}
```

#### 将来フェーズ: 切り替えUI（Phase 2以降）

Phase 2 では `videoUrl` が取得可能になった場合に、AudioVisualizer / Music Video を切り替えるトグルボタンを `media-display` 右上に配置する予定。Phase 1 はフラグなし・実装不要。

```
┌─────────────────────────────┐
│                    [🎬/🎵] │  ← Phase 2: 切り替えボタン（右上）
│  MediaDisplay コンテンツ     │
└─────────────────────────────┘
```

### 3.5 AudioVisualizerコンポーネント仕様

#### 技術仕様

| 項目 | 仕様 |
|------|------|
| 入力 | `<audio>` 要素の `createMediaElementSource`（audioRef 共有） |
| API | `Web Audio API` — `AudioContext` + `AnalyserNode` |
| 描画 | `<canvas>` + `requestAnimationFrame`（60fps） |
| FFTサイズ | `2048`（周波数解像度: 1024バンド） |
| スムージング | `smoothingTimeConstant: 0.8` |
| データ | `getByteFrequencyData()` — 0〜255 の周波数強度配列 |

#### ビジュアルデザイン（WMP/iTunes風 バーグラフ+ミラー）

```
     ▌ ▌▌▌   ▌▌▌▌▌          ← バー上半分（チャンネルカラーグラデーション）
    ▌▌ ▌▌▌  ▌▌▌▌▌▌▌▌
   ▌▌▌ ▌▌▌▌▌▌▌▌▌▌▌▌▌
─────────────────────────── ← 中心線（rgba(255,255,255,0.15)）
   ▐▐▐ ▐▐▐▐▐▐▐▐▐▐▐▐▐        ← ミラー下半分（opacity: var(--viz-mirror-opacity)）
```

| 要素 | 仕様 |
|------|------|
| バー数 | `128` |
| バー色 | `ctx.createLinearGradient` チャンネルカラー（下: 暗 → 上: 明） |
| ミラー | `ctx.save(); ctx.scale(1, -1)` で反転、`globalAlpha = --viz-mirror-opacity` |
| グロー | `ctx.shadowBlur = 15; ctx.shadowColor` = チャンネルアクセント色 |
| 停止時 | `cancelAnimationFrame` → バー高さを 500ms で 0 にアニメーション |

#### デザイントークン

```css
--viz-height: 100%;           /* right-column 内では flex:1 で伸縮 */
--viz-bar-count: 128;
--viz-glow-opacity: 0.6;
--viz-mirror-opacity: 0.3;
```

### 3.6 LyricsDisplay karaoke-overlayモード仕様

#### 概要

`LyricsDisplay` に `mode="karaoke-overlay"` propを渡すことで有効になるカラオケ歌詞オーバーレイモード。MediaDisplay 上に `position: absolute` で重ねる。過去行・現在行・未来行を色と透明度で明確に区別し、現在行を常に中央付近に自動スクロールする。

#### ライン状態定義

| 状態 | 条件 | スタイル |
|------|------|---------|
| **過去行（直前1行）** | `index === activeIndex - 1` | `opacity: 0.4`, `font-size: 0.95rem`, `color: var(--text-secondary)` |
| **過去行（それ以前）** | `index < activeIndex - 1` | `opacity: 0.25`, `font-size: 0.85rem`, `color: var(--text-muted)` |
| **現在行（アクティブ）** | `index === activeIndex` | チャンネルカラーグラデーションテキスト, `font-size: 1.15rem`, `font-weight: 700`, `text-shadow: 0 0 20px accent-glow` |
| **未来行（直後1行）** | `index === activeIndex + 1` | `opacity: 0.75`, `font-size: 1rem`, `color: var(--text-primary)` |
| **未来行（それ以降）** | `index > activeIndex + 1` | `opacity: 0.5`, `font-size: 0.9rem`, `color: var(--text-secondary)` |

#### 自動スクロール

```ts
// アクティブ行が変わるたびに中央へスクロール
useEffect(() => {
  activeLineRef.current?.scrollIntoView({
    behavior: 'smooth',
    block: 'center',
  });
}, [activeIndex]);
```

#### 可読性確保（背景映像との差別化）

```css
.karaoke-line {
  /* テキストシャドウで輪郭を強調 */
  text-shadow:
    0 1px 4px rgba(0, 0, 0, 0.9),
    0 0 8px rgba(0, 0, 0, 0.7);
}

.karaoke-line-active {
  /* アクティブ行は半透明帯で可読性確保 */
  background: rgba(0, 0, 0, 0.45);
  backdrop-filter: blur(4px);
  border-radius: 0.375rem;
  padding: 0.25rem 0.75rem;
}
```

#### CSSレイアウト

```css
.karaoke-overlay {
  position: absolute;
  inset: 0;
  z-index: 10;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  overflow: hidden;
  /* スクロール用の内部コンテナ */
}

.karaoke-scroll-container {
  width: 100%;
  max-height: 100%;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.6rem;
  padding: 2rem 1.5rem;
  scrollbar-width: none;
  -ms-overflow-style: none;
}
.karaoke-scroll-container::-webkit-scrollbar { display: none; }

.karaoke-line {
  text-align: center;
  line-height: 1.5;
  transition: opacity var(--transition-normal) var(--ease-smooth),
              font-size var(--transition-normal) var(--ease-smooth),
              color var(--transition-normal) var(--ease-smooth);
  border-radius: 0.375rem;
  max-width: 90%;
}
```

#### コンポーネントインターフェース

```tsx
// LyricsDisplay の props 拡張（mode="karaoke-overlay" 時に有効）
interface LyricsDisplayProps {
  lyrics: string;        // 改行区切りの歌詞テキスト
  elapsedMs: number;
  durationMs: number;
  channelSlug?: string | null;
}
// ライン進捗: currentIndex = Math.floor((elapsedMs / durationMs) * lines.length)
```

### 3.7 Player — 曲名大表示仕様

```
┌────────────────────────────────────┐
│ ╭──────╮                           │
│╱ SVGリング╲  ◆ トラックタイトル    ◆  │  ← clamp(1.25rem, 2.5vw, 1.875rem)
││ [▶/❚❚] │  チャンネル名             │  ← text-sm text-secondary
│╲        ╱  🔊──────               │
│ ╰──────╯                           │
│ ■■■■■■■□□□□□ プログレスバー          │
└────────────────────────────────────┘
```

| 項目 | 仕様 |
|------|------|
| フォントサイズ | `font-size: clamp(1.25rem, 2.5vw, 1.875rem)` |
| 色 | チャンネルカラーグラデーション（`background-clip: text`） |
| トランケート | `text-overflow: ellipsis`、ホバーで `marquee-scroll` |
| 入場 | 曲切り替え時に `fade-in-up` 300ms |

```css
.now-playing-title {
  font-size: clamp(1.25rem, 2.5vw, 1.875rem);
  font-weight: 700;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  background-clip: text;
  -webkit-background-clip: text;
  color: transparent;
}
.now-playing-title:hover {
  animation: marquee-scroll 8s linear infinite;
  overflow: visible;
}
```

### 3.8 2カラムレイアウト仕様

```css
.app-layout {
  display: grid;
  grid-template-columns: 400px 1fr;
  gap: 1.5rem;
  min-height: 100vh;
  padding: 2rem;
  max-width: 1400px;
  margin: 0 auto;
}

.left-column {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
  overflow-y: auto;
  max-height: calc(100vh - 4rem);
  scrollbar-width: thin;
}

.right-column {
  position: sticky;
  top: 2rem;
  height: calc(100vh - 4rem);
}

/* right-column 内の media-display は全高を占める */
.right-column .media-display {
  height: 100%;
  border-radius: 1rem;
}
```

| ブレークポイント | レイアウト | 左カラム幅 | MediaDisplay高さ |
|---------------|----------|-----------|----------------|
| ≥ 1024px | 2カラム | 400px 固定 | 100vh - 4rem（sticky） |
| 768px – 1023px | 2カラム | 320px 固定 | 100vh - 4rem |
| < 768px | 1カラム（スタック） | 全幅 | 240px |

### 3.9 モバイル対応詳細設計

#### レスポンシブCSS

```css
@media (max-width: 1023px) {
  .app-layout { grid-template-columns: 320px 1fr; }
}

@media (max-width: 767px) {
  .app-layout {
    grid-template-columns: 1fr;
    padding: 1rem;
    gap: 1rem;
  }
  .left-column, .right-column {
    max-height: none;
    position: static;
  }
  .right-column .media-display {
    height: 240px;
  }
  :root {
    --card-channel-height: 140px;
    --card-channel-width: 140px;
    --ring-size: 60px;
  }
}
```

#### タッチ操作性

| 要素 | タッチ対応仕様 |
|------|-------------|
| チャンネルカード | `min-height: 48px`（iOS HIG 推奨タップ領域）|
| 再生/停止ボタン | `min-width: 64px; min-height: 64px`（72px SVGリング） |
| いいねボタン | `padding: 0.75rem`（タップ領域を視覚より広く） |
| 全操作要素 | `touch-action: manipulation`（ダブルタップズーム防止） |
| `:hover` エフェクト | `@media (hover: hover)` で条件付き |

#### スワイプでチャンネル切り替え

```tsx
// ChannelSelector のコンテナにスワイプジェスチャーを追加
// touch-action: pan-x を設定してブラウザのスクロールを許可しつつ検出
const startX = useRef(0);

onTouchStart: (e) => { startX.current = e.touches[0].clientX; }
onTouchEnd: (e) => {
  const diff = startX.current - e.changedTouches[0].clientX;
  if (Math.abs(diff) > 60) {  // 60px スワイプ閾値
    diff > 0 ? selectNextChannel() : selectPrevChannel();
  }
}
```

#### リクエストフォーム — キーボード表示時のレイアウト崩れ防止

```css
/* iOS Safari でキーボード表示時に viewport が縮まる対策 */
.request-form-container {
  /* sticky bottom ではなく、スクロール内に収める */
  position: relative;
}

/* 入力フィールドフォーカス時にフォームを画面内に保つ */
@supports (-webkit-touch-callout: none) {
  .left-column {
    /* iOS Safariのみ: キーボード表示時の min-height を制限しない */
    min-height: unset;
  }
}
```

#### iOS Safari オーディオ自動再生制限

iOS Safari はユーザー操作なしのオーディオ再生を禁止している。対応方針:

1. **初回再生**: チャンネル選択（タップ）のイベントハンドラ内で `audioRef.current.play()` を呼ぶ（ユーザーインタラクション内での呼び出しが必須）
2. **ストリーム切り替え時**: `audioRef.current.load()` → `.play()` をユーザー操作内で実行
3. **自動再生禁止エラー処理**: `play()` が `NotAllowedError` を返した場合、「タップして再生」のオーバーレイを表示

```tsx
// Player.tsx
const togglePlay = async () => {
  if (!audioRef.current || !streamUrl) return;
  try {
    if (isPlaying) {
      audioRef.current.pause();
      setIsPlaying(false);
    } else {
      await audioRef.current.play();  // iOS: ユーザー操作内でのみ成功
      setIsPlaying(true);
    }
  } catch (err) {
    if ((err as DOMException).name === 'NotAllowedError') {
      // タップ促進UIを表示
      setShowPlayPrompt(true);
    }
    setIsPlaying(false);
  }
};
```

#### バックグラウンド再生 — Media Session API

```ts
// 再生中トラック情報を OS に通知（ロック画面・通知センター表示）
useEffect(() => {
  if (!('mediaSession' in navigator)) return;
  if (nowPlaying) {
    navigator.mediaSession.metadata = new MediaMetadata({
      title: nowPlaying.title || nowPlaying.caption || '再生中',
      artist: 'AI Music Station',
      album: activeChannel?.name ?? '',
      // artwork: [{ src: '/icon-512.png', sizes: '512x512', type: 'image/png' }]
    });
    navigator.mediaSession.setActionHandler('play', togglePlay);
    navigator.mediaSession.setActionHandler('pause', togglePlay);
  }
}, [nowPlaying, activeChannel]);
```

#### 低速回線での読み込み最適化

| 対策 | 実装 |
|------|------|
| ストリームプリロード | `<audio preload="none">` — 選択時のみロード開始（現状維持） |
| AudioContext の遅延初期化 | `AudioContext` はユーザー操作（再生ボタン押下）時に初めて生成 |
| Canvas 非表示時の停止 | `isPlaying === false` 時は `cancelAnimationFrame` で描画停止 |
| 画像なし | アートワーク表示なし（Phase 1 スコープ外） |

#### PWA化（将来対応）

Phase 1 では PWA 化は行わない。Phase 2 以降の検討事項として記録:

- `manifest.json` 追加（アイコン・テーマカラー・display: standalone）
- Service Worker によるキャッシュ（UI資産のみ。ストリームはキャッシュ不可）
- `apple-mobile-web-app-capable` メタタグ

### 3.10 デザイン原則

| 原則 | 内容 |
|------|------|
| **没入感優先** | 右カラム全面 MediaDisplay で Music Video / Visualizer + 歌詞オーバーレイのカラオケ体験 |
| **拡張性優先** | MediaDisplay の props で videoUrl を切り替えるだけで Music Video 対応 |
| **ダークモード固定** | `--bg-primary: #0a0a0f` ベースのディープパープル系 |
| **グラスモーフィズム基調** | `backdrop-filter: blur(20px)` + 半透明背景が全カードのベース |
| **チャンネルカラーシステム** | LoFi: 紫 / Anime: ピンク / Jazz: 琥珀 / Game: 緑 — Visualizer・Lyrics・曲名に連動 |
| **GPU合成優先** | `transform` / `opacity` のみ CSS アニメーション対象。Canvas は `requestAnimationFrame` |

### 3.11 デザイントークン拡張方針

既存トークンは一切変更しない。以下カテゴリを `:root` に追加する。

| カテゴリ | 新規トークン | 目的 |
|---------|------------|------|
| ネオモーフィズム影 | `--neo-shadow-out` / `--neo-shadow-in` / `--neo-shadow-button` / `--neo-shadow-button-pressed` | カード浮き上がり・凹み感 |
| カードレイアウト | `--card-channel-width` / `--card-channel-height` / `--card-channel-radius` / `--card-channel-gap` / `--bg-card-elevated` | カードサイズ一元管理 |
| アニメーション | `--transition-fast` / `--transition-normal` / `--transition-slow` / `--ease-bounce` / `--ease-smooth` | 時間・イージング統一 |
| プログレスリング | `--ring-size` / `--ring-stroke` / `--ring-track-color` / `--ring-fill-color` | SVGリング描画 |
| チャンネルアイコン | `--icon-lofi` / `--icon-anime` / `--icon-jazz` / `--icon-game` / `--icon-default` | 絵文字マッピング |
| AudioVisualizer | `--viz-bar-count` / `--viz-glow-opacity` / `--viz-mirror-opacity` | Visualizer 描画パラメータ |

詳細値 → セクション 4（デザイントークン拡張）参照

### 3.12 アニメーション・トランジション仕様

#### 状態別エフェクト

| コンポーネント | 状態変化 | エフェクト | 時間 / イージング |
|--------------|---------|-----------|----------------|
| ChannelCard | 通常 → ホバー | `translateY(-4px)` + shadow強化 | 300ms / `--ease-smooth` |
| ChannelCard | ホバー → 押下 | `scale(0.97)` + `neo-shadow-button-pressed` | 150ms / `--ease-smooth` |
| ChannelCard | 通常 → アクティブ | `channel-gradient-*` + glow border | 即時 |
| PlayButton | 通常 → ホバー | `scale(1.05)` + accent glow | 300ms / `--ease-smooth` |
| PlayButton | 停止 → 再生中 | グラデーション + `glow-pulse` | 300ms / `--ease-smooth` |
| ProgressRing | 進捗変化 | `stroke-dashoffset` | 500ms / linear |
| NowPlayingTitle | 曲切り替え | `fade-in-up` | 300ms / `--ease-smooth` |
| AudioVisualizer | 再生中 | `requestAnimationFrame` ループ（60fps） | — |
| AudioVisualizer | 停止 | バー高さ → 0 | 500ms |
| KaraokeLine | 状態変化 | `opacity` / `font-size` / `text-shadow` | 300ms / `--ease-smooth` |
| KaraokeLine | スクロール | `scrollIntoView({ behavior: 'smooth' })` | ブラウザ依存 |
| MetadataBadge | 入場 | `fade-in-up` stagger（0/80/160/240ms） | 300ms / `--ease-smooth` |
| SuccessMessage | 入場 | `success-pop` | 400ms / `--ease-bounce` |
| InputGlass | フォーカス | `neo-shadow-in` + border-color | 200ms / ease |

#### 新規 @keyframes

| 名前 | 用途 |
|------|------|
| `fade-in-up` | 曲名・バッジ入場 |
| `card-press` | カードタップ強調 |
| `ring-spin` | ローディング中リング |
| `success-pop` | 送信成功メッセージ |
| `marquee-scroll` | 長い曲名ホバー |

```css
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
  /* AudioVisualizer: cancelAnimationFrame で停止 */
}
```

### 3.13 アクセシビリティ要件

| 要素 | 前景色 | コントラスト比 | 判定 |
|------|--------|---------------|------|
| テキスト（primary） | #f0f0f5 | 18.6:1 | ✅ AA |
| テキスト（secondary） | #8b8b9e | 5.1:1 | ✅ AA |
| カラオケアクティブ行 | #f0f0f5 + glow | 17.0:1 | ✅ AA |

| コンポーネント | ARIA |
|--------------|------|
| ChannelCard | `role="radio"`, `aria-checked`, `aria-label` |
| PlayButton | `aria-label="再生" / "一時停止"` |
| AudioVisualizer | `role="img"`, `aria-label="オーディオビジュアライザー"` |
| LyricsDisplay（karaoke-overlay） | `role="log"`, `aria-live="polite"`, `aria-label="歌詞"` |
| MediaDisplay（video時）| `aria-label="Music Video再生中"` |

```css
.focus-ring:focus-visible {
  outline: 2px solid var(--accent-primary);
  outline-offset: 2px;
}
```
---

## 4. デザイントークン拡張

`styles.css` の `:root` に以下のCSS変数を追加する。

### 4.1 ネオモーフィズム用シャドウ

```css
/* Neumorphism shadows */
--neo-shadow-out: 6px 6px 12px rgba(0, 0, 0, 0.4), -6px -6px 12px rgba(255, 255, 255, 0.03);
--neo-shadow-in: inset 4px 4px 8px rgba(0, 0, 0, 0.4), inset -4px -4px 8px rgba(255, 255, 255, 0.03);
--neo-shadow-button: 4px 4px 8px rgba(0, 0, 0, 0.5), -4px -4px 8px rgba(255, 255, 255, 0.04);
--neo-shadow-button-pressed: inset 3px 3px 6px rgba(0, 0, 0, 0.5), inset -3px -3px 6px rgba(255, 255, 255, 0.03);
```

### 4.2 カード・レイアウト用

```css
/* Card dimensions */
--card-channel-width: 160px;
--card-channel-height: 180px;
--card-channel-radius: 1.25rem;
--card-channel-gap: 1rem;

/* Card backgrounds */
--bg-card-elevated: rgba(255, 255, 255, 0.07);
```

### 4.3 アニメーション用

```css
/* Animation timing */
--transition-fast: 150ms;
--transition-normal: 300ms;
--transition-slow: 500ms;
--ease-bounce: cubic-bezier(0.175, 0.885, 0.32, 1.275);
--ease-smooth: cubic-bezier(0.4, 0, 0.2, 1);

/* Progress ring */
--ring-size: 72px;
--ring-stroke: 3px;
--ring-track-color: rgba(255, 255, 255, 0.08);
--ring-fill-color: var(--accent-primary);
```

### 4.4 チャンネルアイコン用

```css
/* Channel icon emoji mapping (used as CSS content) */
--icon-lofi: "🎧";
--icon-anime: "🎤";
--icon-jazz: "🎷";
--icon-game: "🎮";
--icon-default: "🎵";
```

---

## 3. コンポーネント別修正仕様

### 3.1 ChannelSelector — カード型レイアウト化

**現状**: `flex gap-3 flex-wrap` のボタン型リスト。各アイテムは `px-5 py-3 rounded-xl` のフラットボタン。

**変更後**: グリッドレイアウトのカード型。各カードにチャンネルアイコン、名前、メタデータを表示。

#### レイアウト

```
┌──────────────────────────────────────────────────────────────┐
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐       │
│  │  🎧     │  │  🎤     │  │  🎷     │  │  🎮     │       │
│  │         │  │         │  │         │  │         │       │
│  │ Lo-Fi   │  │ Anime   │  │ Jazz    │  │ Game    │       │
│  │ 12曲    │  │ 8曲     │  │ 5曲     │  │ 3件待ち │       │
│  └─────────┘  └─────────┘  └─────────┘  └─────────┘       │
└──────────────────────────────────────────────────────────────┘
```

#### 詳細仕様

| 項目 | 仕様 |
|------|------|
| コンテナ | `display: grid; grid-template-columns: repeat(auto-fill, minmax(var(--card-channel-width), 1fr))` |
| カードサイズ | 幅 `var(--card-channel-width)` 最小、高さ `var(--card-channel-height)` |
| カード間隔 | `var(--card-channel-gap)` = 1rem |
| 角丸 | `var(--card-channel-radius)` = 1.25rem |
| 非アクティブ時背景 | `var(--bg-card)` + `backdrop-filter: blur(20px)` + ネオモーフィズムシャドウ |
| アクティブ時背景 | チャンネル固有グラデーション（既存 `channel-gradient-*`） |
| ホバー時 | `translateY(-4px)` + shadow強化 + border-color変化 |
| タップ時 | `scale(0.97)` + `var(--neo-shadow-button-pressed)` を 150ms |

#### カード内部構造

```tsx
<button
  className={`channel-card focus-ring touch-manipulation ${isActive ? "channel-card-active" : ""} ...`}
  onClick={() => onSelect(channel.slug)}
  aria-label={`${channel.name}チャンネルを選択`}
  aria-pressed={isActive}
>
  {/* アイコン: emoji を背景グラデーション円内に配置 */}
  <div className="channel-card-icon" aria-hidden="true">
    <span>{getChannelIcon(channel.slug)}</span>
  </div>

  {/* チャンネル名 */}
  <div className="channel-card-name">{channel.name}</div>

  {/* メタデータ */}
  <div className="channel-card-meta" aria-label={`${channel.total_tracks}曲${channel.queue_depth > 0 ? `、${channel.queue_depth}件待ち` : ""}`}>
    {channel.total_tracks}曲
    {channel.queue_depth > 0 && ` · ${channel.queue_depth}件待ち`}
  </div>

  {/* アクティブインジケーター */}
  {isActive && <span className="channel-card-active-dot" aria-hidden="true" />}
</button>
```

#### アイコンマッピング関数

```ts
function getChannelIcon(slug: string): string {
  if (slug.includes("lofi") || slug.includes("lo-fi")) return "🎧";
  if (slug.includes("anime")) return "🎤";
  if (slug.includes("jazz")) return "🎷";
  if (slug.includes("game")) return "🎮";
  return "🎵";
}
```

#### CSSクラス追加（styles.css）

```css
.channel-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 0.75rem;
  min-height: var(--card-channel-height);
  padding: 1.5rem 1rem;
  border-radius: var(--card-channel-radius);
  background: var(--bg-card);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border: 1px solid var(--border-glass);
  box-shadow: var(--neo-shadow-out);
  /* transition: all は禁止（NFR-201-1）— GPU合成プロパティのみ明示 */
  transition: transform var(--transition-normal) var(--ease-smooth),
              box-shadow var(--transition-normal) var(--ease-smooth),
              border-color var(--transition-normal) var(--ease-smooth),
              background-color var(--transition-normal) var(--ease-smooth);
  cursor: pointer;
}

/* ホバーエフェクトはポインターデバイスのみ適用（タッチ誤発動防止） */
@media (hover: hover) {
  .channel-card:hover {
    transform: translateY(-4px);
    background: var(--bg-card-elevated);
    border-color: rgba(255, 255, 255, 0.15);
    box-shadow: var(--neo-shadow-out), 0 12px 40px rgba(0, 0, 0, 0.3);
  }
}

.channel-card:active {
  transform: scale(0.97);
  box-shadow: var(--neo-shadow-button-pressed);
  transition-duration: var(--transition-fast);
}

.channel-card-active {
  border-color: rgba(255, 255, 255, 0.25);
  box-shadow: 0 0 24px var(--accent-glow), var(--neo-shadow-out);
}

.channel-card-icon {
  width: 3rem;
  height: 3rem;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.5rem;
  background: rgba(255, 255, 255, 0.06);
  box-shadow: var(--neo-shadow-button);
}

.channel-card-name {
  font-size: 0.875rem;
  font-weight: 600;
  text-align: center;
  color: var(--text-primary);
}

.channel-card-meta {
  font-size: 0.7rem;
  color: var(--text-secondary);
  text-align: center;
}

/* アクティブインジケータードット（glow-pulse アニメーション適用） */
.channel-card-active-dot {
  position: absolute;
  top: 0.5rem;
  right: 0.5rem;
  width: 0.5rem;
  height: 0.5rem;
  border-radius: 50%;
  background-color: rgba(255, 255, 255, 0.8);
  animation: glow-pulse 2s ease-in-out infinite;
}
```

---

### 3.2 Player — プログレスリング・再生ボタン強化

**現状**: 64px円形ボタン + 線形プログレスバー（shimmer）。

**変更後**: 再生ボタンをSVGプログレスリングで囲み、再生経過を視覚化。ボタンにネオモーフィズム効果。

#### プログレスリング仕様

```
    ╭──────╮
   ╱  ▶/❚❚  ╲    ← SVG circle (stroke-dasharray で進捗表示)
  │          │
   ╲        ╱
    ╰──────╯
```

| 項目 | 仕様 |
|------|------|
| サイズ | `var(--ring-size)` = 72px |
| ストローク幅 | `var(--ring-stroke)` = 3px |
| トラック色 | `var(--ring-track-color)` = rgba(255,255,255,0.08) |
| 進捗色 | `var(--ring-fill-color)` = var(--accent-primary) |
| 進捗計算 | `stroke-dashoffset = circumference * (1 - elapsedMs / durationMs)` |
| アニメーション | `transition: stroke-dashoffset 0.5s ease` |

#### 実装概要

```tsx
function ProgressRing({ progress, size = 72, stroke = 3 }: {
  progress: number; // 0-1
  size?: number;
  stroke?: number;
}) {
  const radius = (size - stroke) / 2;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference * (1 - Math.min(progress, 1));

  return (
    <svg width={size} height={size} className="absolute inset-0 -rotate-90">
      {/* Track */}
      <circle
        cx={size / 2} cy={size / 2} r={radius}
        fill="none"
        stroke="var(--ring-track-color)"
        strokeWidth={stroke}
      />
      {/* Progress */}
      <circle
        cx={size / 2} cy={size / 2} r={radius}
        fill="none"
        stroke="var(--ring-fill-color)"
        strokeWidth={stroke}
        strokeDasharray={circumference}
        strokeDashoffset={offset}
        strokeLinecap="round"
        style={{ transition: 'stroke-dashoffset 0.5s ease' }}
      />
    </svg>
  );
}
```

#### 再生ボタンのネオモーフィズム化

```css
.player-button {
  position: relative;
  width: var(--ring-size);
  height: var(--ring-size);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--bg-card-elevated);
  box-shadow: var(--neo-shadow-button);
  transition: transform var(--transition-normal) var(--ease-smooth),
              box-shadow var(--transition-normal) var(--ease-smooth),
              background var(--transition-normal) var(--ease-smooth);
}

.player-button:hover:not(:disabled) {
  transform: scale(1.05);
  box-shadow: var(--neo-shadow-button), 0 0 20px var(--accent-glow);
}

.player-button:active:not(:disabled) {
  box-shadow: var(--neo-shadow-button-pressed);
  transform: scale(0.97);
  transition-duration: var(--transition-fast);
}

.player-button-playing {
  background: linear-gradient(135deg, var(--accent-primary), #7c3aed);
  box-shadow: var(--neo-shadow-button), 0 0 24px var(--accent-glow);
}
```

#### 既存プログレスバー変更

線形プログレスバー（`.progress-glow`）は維持。ただし `shimmer` アニメーションに加え、`nowPlaying` のトラック進捗を `width` で反映する。

```tsx
{/* Playing progress bar */}
{isPlaying && (
  <div className="mt-4 h-0.5 rounded-full overflow-hidden bg-white/5">
    <div
      className="h-full rounded-full bg-gradient-to-r from-indigo-500 via-purple-500 to-pink-500 progress-glow"
      style={{
        width: `${progress * 100}%`,
        transition: 'width 0.5s linear',
      }}
    />
  </div>
)}
```

Player に `elapsedMs` / `durationMs` props を追加し、App.tsx から渡す。

---

### 3.3 NowPlaying — 視覚強化

**現状**: glass-card に再生中ドット + タイトル + メタデータバッジ。

**変更後**:

#### 変更点

1. **パルスアニメーション強化**: 再生中ドットを `glow-pulse` クラスに変更（現在 `animate-pulse`）
2. **グラデーション背景の動的化**: チャンネルスラグに応じて `channel-gradient-*` のグラデーションを使用
3. **入場アニメーション**: `slide-up` に加え、メタデータバッジに `stagger-fade-in` を追加

#### CSS追加

```css
/* Stagger fade in for child elements */
.stagger-fade-in > * {
  opacity: 0;
  animation: fade-in-up var(--transition-normal) var(--ease-smooth) forwards;
}

.stagger-fade-in > *:nth-child(1) { animation-delay: 0ms; }
.stagger-fade-in > *:nth-child(2) { animation-delay: 80ms; }
.stagger-fade-in > *:nth-child(3) { animation-delay: 160ms; }
.stagger-fade-in > *:nth-child(4) { animation-delay: 240ms; }

@keyframes fade-in-up {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
}
```

#### メタデータバッジのネオモーフィズム化

現在の `bg-white/5` バッジに `var(--neo-shadow-in)` の軽量版を適用:

```css
.badge-neo {
  background: rgba(255, 255, 255, 0.05);
  box-shadow: inset 2px 2px 4px rgba(0, 0, 0, 0.3), inset -2px -2px 4px rgba(255, 255, 255, 0.02);
  border-radius: 9999px;
  padding: 0.125rem 0.5rem;
}
```

---

### 3.4 TrackHistory — ホバー・展開アニメーション

**現状**: `glass-card-hover` のリスト、展開時にアニメーションなし。

**変更後**:

#### 変更点

1. **ホバーエフェクト強化**: 左側にチャンネルカラーのアクセントライン表示
2. **展開アニメーション**: 歌詞展開時に `max-height` + `opacity` のトランジションを追加
3. **リスト入場アニメーション**: 各アイテムに stagger 付き `slide-up`

#### CSSクラス追加

```css
/* Track history item hover accent */
.track-item {
  position: relative;
  overflow: hidden;
  transition: background-color var(--transition-normal) var(--ease-smooth),
              box-shadow var(--transition-normal) var(--ease-smooth);
}

.track-item::before {
  content: "";
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 3px;
  background: var(--accent-primary);
  opacity: 0;
  transition: opacity var(--transition-fast);
}

.track-item:hover::before {
  opacity: 1;
}

/* Expandable content animation */
.expand-content {
  max-height: 0;
  opacity: 0;
  overflow: hidden;
  transition: max-height var(--transition-slow) var(--ease-smooth),
              opacity var(--transition-normal) var(--ease-smooth);
}

.expand-content-open {
  max-height: 500px;
  opacity: 1;
}
```

#### 実装変更ポイント

```tsx
{/* 展開部分 — 常にレンダリングし、CSSクラスで開閉 */}
{track.lyrics && (
  <div className={`expand-content ${isExpanded ? "expand-content-open" : ""}`}>
    <div className="px-4 pb-3">
      <LyricsDisplay lyrics={track.lyrics} elapsedMs={0} durationMs={0} />
    </div>
  </div>
)}
```

---

### 3.5 RequestForm — フォーム視覚改善

**現状**: `glass-card` + `input-glass` フォーム。送信ボタンはグラデーション。

**変更後**:

#### 変更点

1. **入力フィールドのフォーカスアニメーション強化**: フォーカス時にネオモーフィズム inset shadow に変化
2. **送信ボタンのネオモーフィズム化**: hover/active にソフトシャドウ
3. **成功/エラーメッセージの入場アニメーション**: `slide-up` を付与

#### CSS変更

```css
.input-glass:focus {
  outline: none;
  border-color: var(--accent-primary);
  box-shadow: var(--neo-shadow-in), 0 0 0 3px var(--accent-glow);
  background: rgba(255, 255, 255, 0.08);
}

.btn-submit {
  position: relative;
  padding: 0.625rem 1.25rem;
  border-radius: 0.75rem;
  font-size: 0.875rem;
  font-weight: 600;
  color: white;
  background: linear-gradient(135deg, var(--accent-primary), #7c3aed);
  box-shadow: var(--neo-shadow-button);
  transition: transform var(--transition-normal) var(--ease-smooth),
              box-shadow var(--transition-normal) var(--ease-smooth);
}

.btn-submit:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: var(--neo-shadow-button), 0 8px 24px var(--accent-glow);
}

.btn-submit:active:not(:disabled) {
  transform: translateY(0);
  box-shadow: var(--neo-shadow-button-pressed);
  transition-duration: var(--transition-fast);
}
```

---

## 4. アニメーション定義

### 4.1 新規追加アニメーション

| アニメーション名 | 用途 | タイミング |
|----------------|------|----------|
| `fade-in-up` | メタデータバッジ stagger 入場 | 300ms, ease-smooth |
| `card-press` | チャンネルカードタップ | 150ms, ease-bounce |
| `ring-spin` | プログレスリング（ストリーム中ローディング時） | 1.5s, linear, infinite |
| `expand` | TrackHistory歌詞展開 | 500ms (max-height), 300ms (opacity) |
| `success-pop` | RequestForm成功メッセージ | 400ms, ease-bounce |

### 4.2 既存アニメーション変更

| アニメーション | 変更内容 |
|--------------|---------|
| `glow-pulse` | 変更なし（ChannelSelector のアクティブドットに引き続き使用） |
| `slide-up` | 変更なし（入場アニメーションに引き続き使用） |
| `shimmer` | 変更なし（プログレスバーに引き続き使用） |
| `visualizer-bounce` | 変更なし |
| `reaction-pop` / `reaction-float` | 変更なし |

### 4.3 CSS @keyframes 追加

```css
@keyframes fade-in-up {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
}

@keyframes card-press {
  0% { transform: scale(1); }
  50% { transform: scale(0.95); }
  100% { transform: scale(1); }
}

@keyframes ring-spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

@keyframes success-pop {
  0% { opacity: 0; transform: scale(0.9) translateY(8px); }
  60% { transform: scale(1.02) translateY(0); }
  100% { opacity: 1; transform: scale(1) translateY(0); }
}

/* 長い曲名のマーキースクロール（FR-108-3） */
@keyframes marquee-scroll {
  0%   { transform: translateX(0); }
  100% { transform: translateX(-100%); }
}
```

**marquee-scroll の overflow/clip 設計**:
```css
/* ラッパー: はみ出しを clip でトリミング */
.now-playing-title-wrapper {
  overflow: hidden;           /* はみ出しを非表示 */
  white-space: nowrap;
  position: relative;
}

/* テキスト本体: ホバー時にマーキー発動 */
.now-playing-title {
  display: inline-block;
  white-space: nowrap;
  /* デフォルト: truncate */
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 100%;
}

/* ホバー時: ellipsis → marquee に切り替え */
@media (hover: hover) {
  .now-playing-title-wrapper:hover .now-playing-title {
    overflow: visible;          /* clip を解除してテキスト全体を流す */
    text-overflow: clip;
    animation: marquee-scroll 8s linear infinite;
  }
}
```

---

## 5. レスポンシブ戦略

### 5.1 ブレークポイント

| ブレークポイント | チャンネルカード列数 | 備考 |
|----------------|-------------------|------|
| < 480px | 2列 | `grid-template-columns: repeat(2, 1fr)` |
| 480px – 640px | 3列 | カード高さ縮小（160px） |
| > 640px | `auto-fill, minmax(160px, 1fr)` | デフォルト |

### 5.2 モバイル（< 640px）での調整

```css
@media (max-width: 639px) {
  :root {
    --card-channel-height: 150px;
    --ring-size: 60px;
  }

  /* Player: 縦積みレイアウト */
  .player-layout {
    flex-direction: column;
    align-items: center;
    text-align: center;
  }

  /* Volume control: フル幅 */
  .volume-control {
    width: 100%;
    justify-content: center;
  }
}

@media (max-width: 479px) {
  :root {
    --card-channel-width: 140px;
    --card-channel-height: 140px;
  }
}
```

### 5.3 タッチ対応

- ホバーエフェクト: `@media (hover: hover)` で条件付き適用
- タップフィードバック: `:active` による `scale(0.97)` は全デバイスで適用
- `touch-action: manipulation` を操作要素に付与（ダブルタップズーム防止）

---

## 6. アクセシビリティ要件

### 6.1 コントラスト比

| 要素 | 前景色 | 背景色 | コントラスト比 | 基準 |
|------|--------|--------|---------------|------|
| テキスト（primary） | #f0f0f5 | #0a0a0f | 18.6:1 | WCAG AA 4.5:1 ✅ |
| テキスト（secondary） | #8b8b9e | #0a0a0f | 5.1:1 | WCAG AA 4.5:1 ✅ |
| テキスト（muted） | #5a5a6e | #0a0a0f | 3.2:1 | 装飾テキストのみに使用 |
| ボタンテキスト | #ffffff | gradient bg | 7.0:1以上 | WCAG AA ✅ |

### 6.2 キーボード操作

| 操作 | キー | 動作 |
|------|-----|------|
| チャンネル選択 | Tab / Shift+Tab | カード間フォーカス移動 |
| チャンネル選択 | Enter / Space | チャンネル選択 |
| 再生/停止 | Enter / Space | 再生トグル |
| 音量調整 | ← / → | ±5% |
| 歌詞展開 | Enter / Space | TrackHistory アイテム展開/折畳 |

### 6.3 フォーカスインジケーター

```css
/* フォーカスリングの統一スタイル */
.focus-ring:focus-visible {
  outline: 2px solid var(--accent-primary);
  outline-offset: 2px;
}
```

すべてのインタラクティブ要素に `focus-ring` クラスまたは同等の `:focus-visible` スタイルを適用する。

### 6.4 アニメーション配慮

```css
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}
```

---

## 7. 修正対象ファイル一覧

| ファイル | 変更内容 |
|---------|---------|
| `frontend/src/styles.css` | デザイントークン追加、新CSSクラス・アニメーション追加 |
| `frontend/src/components/ChannelSelector.tsx` | カード型レイアウトに全面書き換え |
| `frontend/src/components/Player.tsx` | ProgressRing追加、ボタンネオモーフィズム化、props追加 |
| `frontend/src/components/NowPlaying.tsx` | 動的グラデーション、stagger入場、バッジ強化 |
| `frontend/src/components/TrackHistory.tsx` | ホバーアクセント、展開アニメーション |
| `frontend/src/components/RequestForm.tsx` | ボタン・入力フィールド視覚強化 |
| `frontend/src/App.tsx` | Player に `elapsedMs` / `durationMs` props 追加 |

---

## 8. テスト方針

### 8.1 ビルドテスト

- `npm run build` が警告なしで成功すること
- TypeScript型エラーがないこと

### 8.2 コンポーネント別テスト観点

| コンポーネント | テスト観点 |
|--------------|----------|
| ChannelSelector | カードが正しくグリッド表示されること / アクティブ状態の切替 / チャンネル情報（曲数・キュー深度）の表示 / レスポンシブ列数 |
| Player | プログレスリングの進捗表示 / 再生/停止ボタンの状態遷移 / ネオモーフィズムシャドウの適用 |
| NowPlaying | チャンネルに応じたグラデーション背景 / メタデータバッジの stagger 表示 |
| TrackHistory | ホバー時アクセントライン / 歌詞展開の開閉アニメーション / 展開状態トグル |
| RequestForm | フォーカス時 inset shadow / 送信ボタンの hover/active エフェクト / 成功メッセージ入場アニメーション |

### 8.3 クロスブラウザ

- Chrome (latest), Safari (latest), Firefox (latest)
- backdrop-filter: Safari prefixの確認
- ネオモーフィズム shadow: 各ブラウザでの描画確認

### 8.4 レスポンシブテスト

- 320px / 480px / 640px / 768px / 1024px の各幅でレイアウト崩れがないこと
- チャンネルカードのグリッド列数が正しく切り替わること
- Player のモバイルレイアウト（縦積み）が正しいこと

### 8.5 アクセシビリティテスト

- Tab キーでの全インタラクティブ要素フォーカス
- `prefers-reduced-motion` 時のアニメーション無効化
- スクリーンリーダー（VoiceOver）での操作確認

### 8.6 パフォーマンス

- `animation` / `transition` は GPU 合成プロパティ（`transform`, `opacity`）のみ使用
  - `box-shadow` のトランジションは `transition: box-shadow` で明示し、レイアウトシフトを防止
- 不要なリレンダリングの回避（ProgressRing の props メモ化検討）

---

## 9. API/DB 設計

> **担当**: System Engineer
> **方針**: UI刷新 Phase 1 はビジュアル・インタラクションの変更に特化しており、**バックエンドAPI・DBスキーマの変更は不要**。既存APIで全データが揃っている。

---

### 9.1 既存APIエンドポイント一覧

| # | メソッド | パス | 説明 | UI刷新での使用 |
|---|---------|------|------|--------------|
| 1 | GET | `/api/channels` | アクティブチャンネル一覧 | ChannelSelector カード表示 ✅ |
| 2 | GET | `/api/channels/{slug}` | チャンネル詳細 | ChannelManager ✅ |
| 3 | POST | `/api/channels` | チャンネル作成 | ChannelManager ✅ |
| 4 | PUT | `/api/channels/{slug}` | チャンネル全体更新 | ChannelManager ✅ |
| 5 | PATCH | `/api/channels/{slug}` | チャンネル部分更新 | ChannelManager ✅ |
| 6 | DELETE | `/api/channels/{slug}` | チャンネル削除（論理削除） | ChannelManager ✅ |
| 7 | GET | `/api/channels/{slug}/tracks` | トラック一覧（ページネーション） | TrackHistory ✅ |
| 8 | GET | `/api/channels/{slug}/now-playing` | 現在再生中トラック | Player/NowPlaying ✅ |
| 9 | POST | `/api/channels/{slug}/requests` | 楽曲リクエスト作成 | RequestForm ✅ |
| 10 | GET | `/api/channels/{slug}/requests` | リクエスト一覧 | （管理用） |
| 11 | GET | `/api/requests/{request_id}` | リクエスト詳細 | （管理用） |
| 12 | POST | `/api/tracks/{track_id}/reactions` | リアクション追加 | ReactionButton ✅ |
| 13 | DELETE | `/api/tracks/{track_id}/reactions` | リアクション削除 | ReactionButton ✅ |
| 14 | GET | `/api/tracks/{track_id}/reactions` | リアクション状態取得 | ReactionButton ✅ |

**新規エンドポイント**: なし

---

### 9.2 UI刷新で使用する主要フィールド

#### ChannelSelector カード型表示に必要なフィールド

`GET /api/channels` レスポンス（`ChannelResponse`）から取得:

| フィールド | 型 | 用途 | 既存? |
|-----------|---|------|------|
| `slug` | `string` | アイコンマッピング（lofi/anime/jazz/game） | ✅ 既存 |
| `name` | `string` | カード名称表示 | ✅ 既存 |
| `total_tracks` | `int` | カードメタデータ「N曲」表示 | ✅ 既存 |
| `queue_depth` | `int` | カードメタデータ「N件待ち」表示 | ✅ 既存 |
| `is_active` | `bool` | アクティブチャンネルフィルタリング | ✅ 既存 |

#### Player プログレスリングに必要なフィールド

`GET /api/channels/{slug}/now-playing` レスポンス（`NowPlayingResponse` → `Track`）から取得:

| フィールド | 型 | 用途 | 既存? |
|-----------|---|------|------|
| `track.duration_ms` | `int \| null` | プログレスリングの `durationMs` | ✅ 既存 |
| `track.id` | `string` | トラック変更検知（elapsedMs リセット） | ✅ 既存 |

`elapsedMs` は App.tsx の `setInterval`（500ms）で管理済み（バックエンド不要）。

---

### 9.3 データモデル（変更なし）

既存5テーブルの変更は不要。参考として現状を記録する。

```
channels          requests          tracks
─────────         ─────────         ─────────
id (PK)           id (PK)           id (PK)
slug              channel_id (FK)   request_id (FK, unique)
name              status            channel_id (FK)
description       mood              file_path
is_active         caption           duration_ms   ← プログレスリング用
default_bpm_*     lyrics            title
default_duration  bpm               caption
prompt_template   duration          mood / lyrics
auto_generate     music_key         bpm / music_key
min_stock         created_at        play_count
max_stock         started_at        like_count
                  completed_at      is_retired
                  error_message     created_at

now_playing       reactions
─────────         ─────────
channel_id (PK)   id (PK)
track_id (FK)     track_id (FK)
started_at        session_id
                  reaction_type
                  created_at
```

**DBインデックス（既存、変更なし）**:

| インデックス名 | 対象カラム | 条件 |
|-------------|---------|------|
| `idx_requests_pending` | `(status, created_at)` | WHERE status='pending' |
| `idx_requests_channel` | `(channel_id, status)` | — |
| `idx_tracks_channel` | `(channel_id, created_at)` | — |
| `idx_reactions_track` | `(track_id)` | — |

---

### 9.4 フロントエンド-バックエンド間インターフェース定義

#### 変更が必要なフロントエンド型定義

`Player` コンポーネントへの props 追加（TypeScript型変更のみ、APIは無変更）:

```typescript
// frontend/src/components/Player.tsx — Props 変更（追加のみ）
interface PlayerProps {
  streamUrl: string | null;
  channelName: string;
  nowPlaying: Track | null;
  elapsedMs: number;     // 追加: App.tsx から渡す
  durationMs: number;    // 追加: nowPlaying.duration_ms ?? 0
}
```

```typescript
// frontend/src/App.tsx — Player 呼び出し箇所変更
<Player
  streamUrl={streamUrl}
  channelName={activeChannel?.name ?? ""}
  nowPlaying={nowPlaying}
  elapsedMs={elapsedMs}                    // 追加（既存 state を再利用）
  durationMs={nowPlaying?.duration_ms ?? 0} // 追加
/>
```

#### ポーリング戦略（変更なし）

| エンドポイント | ポーリング間隔 | Hook |
|--------------|-------------|------|
| `GET /api/channels` | 起動時1回のみ | `useChannels` |
| `GET /api/channels/{slug}/now-playing` | 5,000ms | `useNowPlaying` |

---

### 9.5 パフォーマンス考慮事項

#### バックエンド側

| 項目 | 評価 | 対応方針 |
|-----|------|---------|
| `GET /api/channels` の N+1 | 各チャンネルで queue_depth・total_tracks を個別 SELECT。チャンネル数増加時に問題になりうる | Phase 1 では許容。将来は JOIN + GROUP BY に最適化 |
| `now-playing` 5秒ポーリング | チャンネル数 × アクティブユーザー数のリクエスト発生 | Caddy リバースプロキシでの短期キャッシュ（`max-age=3`）が有効。Phase 1 では変更なし |
| `total_tracks` の精度 | `is_retired` フィルタなしでカウント（retired トラックも含む） | UIでの表示上は許容範囲。Phase 1 では変更なし |

#### フロントエンド側

| 項目 | 対応方針 |
|-----|---------|
| ProgressRing の再レンダリング | `elapsedMs` が 500ms ごとに変化するため、`React.memo` で囲み `progress`（0-1 の float）のみ比較してリレンダリング抑制 |
| CSS トランジション | `transform` / `opacity` のみをアニメーション対象とし GPU 合成を活用。`box-shadow` は明示的に `transition` プロパティ指定 |
| グリッドレイアウト | `auto-fill, minmax()` で DOM 変更なくリフロー対応。追加ライブラリ不要 |

---

### 9.6 変更対象ファイル（API/DB 観点）

| ファイル | 変更内容 | 種別 |
|---------|---------|------|
| `frontend/src/components/Player.tsx` | `elapsedMs` / `durationMs` props 型定義追加 | フロントエンド |
| `frontend/src/App.tsx` | Player に `elapsedMs` / `durationMs` を渡す | フロントエンド |
| バックエンド全般 | **変更なし** | — |
| DBスキーマ全般 | **変更なし** | — |

---

## 10. テスト設計（QA Engineer）

> **作成**: QA Engineer / 作成日: 2026-03-22

### 10.1 テスト戦略

本 Phase 1 は CSS/アニメーション中心の UI 刷新であり、ロジック変更は `getChannelIcon`・`ProgressRing` の計算部分に限られる。ただし Gate 5 合格のため、**モックのみのテストは不合格**とし、以下の3層を必須とする。

| レイヤー | ツール | 用途 | 必須 |
|---------|--------|------|------|
| 単体テスト | Vitest + React Testing Library | ロジック・コンポーネントレンダリング | ✅ |
| 結合テスト | Vitest + jsdom（APIモックなし層） | コンポーネント間の状態連携 | ✅ |
| E2Eテスト | Playwright | ブラウザ上の見た目・アニメーション・レスポンシブ・アクセシビリティ | ✅ |

> **注意**: 現リポジトリには Playwright が未導入のため、実装フェーズ（Gate 3）で `@playwright/test` の追加と `playwright.config.ts` の作成が必要。

---

### 10.2 単体テスト仕様

#### 10.2.1 `getChannelIcon` 関数

ファイル: `frontend/src/__tests__/getChannelIcon.test.ts`

| # | テストケース | 入力 `slug` | 期待値 |
|---|------------|------------|--------|
| U-01 | lofi slug | `"lofi"` | `"🎧"` |
| U-02 | lo-fi（ハイフン）slug | `"lo-fi-beats"` | `"🎧"` |
| U-03 | anime slug | `"anime-songs"` | `"🎤"` |
| U-04 | jazz slug | `"jazz-station"` | `"🎷"` |
| U-05 | game slug | `"game-music"` | `"🎮"` |
| U-06 | 未知 slug | `"classical"` | `"🎵"` |
| U-07 | 空文字 | `""` | `"🎵"` |

#### 10.2.2 `ProgressRing` コンポーネント

ファイル: `frontend/src/__tests__/ProgressRing.test.tsx`

| # | テストケース | 入力 | 期待値 |
|---|------------|------|--------|
| U-08 | 進捗0% | `progress=0` | `strokeDashoffset` = 周長全体 |
| U-09 | 進捗50% | `progress=0.5` | `strokeDashoffset` = 周長の半分 |
| U-10 | 進捗100% | `progress=1` | `strokeDashoffset` = 0 |
| U-11 | 進捗超過クランプ | `progress=1.5` | `strokeDashoffset` ≥ 0（`Math.min(progress, 1)` で上限制限） |
| U-12 | SVGサイズ | `size=72, stroke=3` | SVG width/height が 72、circle の r が 34.5 |
| U-13 | デフォルトサイズ | props未指定 | `size=72, stroke=3` で描画 |

#### 10.2.3 `ChannelSelector` — カード型対応

ファイル: `frontend/src/__tests__/ChannelSelector.test.tsx`（既存に追記）

| # | テストケース | 詳細 |
|---|------------|------|
| U-14 | チャンネル名表示 | 各チャンネルのname がカード内に表示される（既存） |
| U-15 | onSelect呼び出し | カードクリックで `onSelect(slug)` が呼ばれる（既存） |
| U-16 | 非アクティブ非表示 | `is_active=false` のチャンネルが表示されない（既存） |
| U-17 | **チャンネルアイコン表示** | slug に応じた絵文字が表示される（新規） |
| U-18 | **total_tracks表示** | `"10曲"` の形式でトラック数が表示される（新規） |
| U-19 | **queue_depth表示** | queue_depth > 0 の場合 `"2件待ち"` が表示される（新規） |
| U-20 | **queue_depth非表示** | queue_depth = 0 の場合 件待ち表記が表示されない（新規） |
| U-21 | **アクティブドット** | activeSlug 一致時に `channel-card-active-dot` 要素が存在する（新規） |
| U-22 | **非アクティブ時ドットなし** | activeSlug 不一致時にアクティブドットが存在しない（新規） |

#### 10.2.4 `Player` — ProgressRing統合・props拡張

ファイル: `frontend/src/__tests__/Player.test.tsx`（既存に追記）

| # | テストケース | 詳細 |
|---|------------|------|
| U-23 | チャンネル名表示（既存） | — |
| U-24 | プレースホルダー（既存） | — |
| U-25 | 再生ボタン存在（既存） | — |
| U-26 | ストリームなし時disable（既存） | — |
| U-27 | **ProgressRingレンダリング** | `elapsedMs=90000, durationMs=180000` でSVG要素が存在する（新規） |
| U-28 | **progress=0時** | `elapsedMs=0` でProgressRingのstrokeDashoffset = 周長（新規） |
| U-29 | **streamUrlなし時ProgressRing非表示** | streamUrl=null 時にSVGが存在しない（新規） |
| U-30 | **player-button-playing クラス** | 再生状態でボタンに `player-button-playing` クラスが付与（新規） |

#### 10.2.5 `NowPlaying` — 動的グラデーション対応

ファイル: `frontend/src/__tests__/NowPlaying.test.tsx`（既存に追記）

| # | テストケース | 詳細 |
|---|------------|------|
| U-31 | キャプション表示（既存） | — |
| U-32 | BPM表示（既存） | — |
| U-33 | **channelSlug props追加** | `channelSlug="lofi"` を渡してエラーなくレンダリング（新規） |
| U-34 | **lofi グラデーションクラス** | `channelSlug="lofi"` で `channel-gradient-lofi` クラスが存在（新規） |
| U-35 | **stagger-fade-in クラス** | バッジコンテナに `stagger-fade-in` クラスが存在（新規） |

#### 10.2.6 `TrackHistory` — 展開アニメーション対応

ファイル: `frontend/src/__tests__/TrackHistory.test.tsx`（既存に追記）

| # | テストケース | 詳細 |
|---|------------|------|
| U-36 | トラックタイトル表示（既存） | — |
| U-37 | ReactionButton表示（既存） | — |
| U-38 | 歌詞展開（既存） | — |
| U-39 | **expand-content クラス** | lyrics有りトラックに `expand-content` 要素が存在する（新規） |
| U-40 | **展開時クラス付与** | クリック後に `expand-content-open` クラスが付与される（新規） |
| U-41 | **折畳時クラス除去** | 再クリックで `expand-content-open` クラスが除去される（新規） |
| U-42 | **track-item クラス** | 各トラック行に `track-item` クラスが存在する（新規） |

#### 10.2.7 `RequestForm` — フォーカス・送信強化

ファイル: `frontend/src/__tests__/RequestForm.test.tsx`（既存に追記）

| # | テストケース | 詳細 |
|---|------------|------|
| U-43 | フォームフィールド存在（既存） | — |
| U-44 | 送信ボタン有効（既存） | — |
| U-45 | **btn-submit クラス** | 送信ボタンに `btn-submit` クラスが存在する（新規） |
| U-46 | **input-glass クラス** | テキストエリアに `input-glass` クラスが存在する（新規） |
| U-47 | **成功メッセージ表示** | API成功後に成功メッセージ要素が表示される（新規、APIモック使用） |
| U-48 | **成功メッセージに slide-up** | 成功メッセージ要素に `slide-up` クラスが存在する（新規） |

---

### 10.3 結合テスト仕様

チャンネル選択 → プレーヤー再生 → NowPlaying更新 の状態フローを App レベルで検証する。
APIコールは vitest のモジュールモックを用いるが、**コンポーネント間の状態連携は実際のReactレンダリングで確認**する。

> **【DB結合テストの代替方針】** 本 Phase 1 はフロントエンド専用変更のため、実DB接続の結合テストは E2Eテスト（Docker Compose 起動による実アプリ + 実DB環境）で代替する。

ファイル: `frontend/src/__tests__/integration/ChannelSelectToPlay.test.tsx`

| # | テストケース | 詳細 |
|---|------------|------|
| I-01 | チャンネル選択→Player更新 | lofiカードクリック → Player の channelName が更新される |
| I-02 | アクティブカード状態同期 | チャンネル選択後、選択チャンネルカードに `channel-card-active` クラスが付く |
| I-03 | NowPlaying連携 | APIモック経由でnowPlayingが更新された後、NowPlayingコンポーネントにタイトルが表示される |
| I-04 | ProgressRing進捗連携 | `elapsedMs` が変化するとProgressRingのSVGが更新される |
| I-05 | TrackHistory更新 | チャンネル切替後、TrackHistoryがリフェッチされる |

---

### 10.4 E2Eテスト仕様

ツール: **Playwright** (`@playwright/test`)
対象環境: `docker compose up` でアプリ起動後、`http://localhost:3200` に対してテスト実行

> Playwright は実装フェーズで `frontend/` に追加する。`playwright.config.ts` の `baseURL` は `http://localhost:3200` で設定。

#### 10.4.1 レイアウト・ビジュアル検証

| # | テストケース | 検証方法 |
|---|------------|---------|
| E-01 | チャンネルカードグリッド表示 | `display: grid` が適用されていること（`evaluate(getComputedStyle)`） |
| E-02 | デスクトップ (1024px) カード列数 | `auto-fill` により4列以上のカードが表示される |
| E-03 | タブレット (640px) カード列数 | 3列のカードが表示される |
| E-04 | モバイル (480px) カード列数 | 2列のカードが表示される |
| E-05 | カードアイコン絵文字表示 | `🎧` `🎤` `🎷` `🎮` がDOM上に存在する |
| E-06 | ProgressRingのSVG描画 | 再生開始後にSVG要素が visible である |
| E-07 | プログレスバー幅変化 | 再生30秒後に `.progress-glow` の width が > 0% になっている |

#### 10.4.2 インタラクション検証

| # | テストケース | 検証方法 |
|---|------------|---------|
| E-08 | カードホバーアニメーション | hover後に `transform: translateY(-4px)` が computedStyle に存在する |
| E-09 | カードクリック選択 | カードクリック → Player のチャンネル名更新 + `channel-card-active` クラス付与 |
| E-10 | 歌詞展開アニメーション | TrackHistoryアイテムクリック → `expand-content-open` クラス付与確認 |
| E-11 | 歌詞折畳アニメーション | 再クリック → `expand-content-open` クラス除去確認 |
| E-12 | フォームフォーカス効果 | textarea フォーカス → `border-color` が accent-primary に変化 |

#### 10.4.3 アクセシビリティ検証

| # | テストケース | 検証方法 |
|---|------------|---------|
| E-13 | Tabキーフォーカス移動 | Tab キーでチャンネルカード全件フォーカス可能 |
| E-14 | Enterキーチャンネル選択 | カードフォーカス時 Enter → チャンネル選択される |
| E-15 | フォーカスリング表示 | `:focus-visible` 時に outline が visible |
| E-16 | prefers-reduced-motion | `page.emulateMedia({ reducedMotion: 'reduce' })` → transition-duration が 0.01ms |
| E-17 | aria-label 存在 | 再生ボタン `aria-label="再生"` が存在する |

#### 10.4.4 クロスブラウザ検証

| ブラウザ | 確認観点 |
|---------|---------|
| Chromium (latest) | 全E2Eテスト実行（基準） |
| Firefox (latest) | ネオモーフィズム shadow 描画、backdrop-filter フォールバック |
| WebKit/Safari (latest) | `-webkit-backdrop-filter` 動作確認 |

Playwright の `projects` 設定で `chromium` / `firefox` / `webkit` の3プロジェクトを定義する。

---

### 10.5 受入基準

| ゲート | 基準 |
|-------|------|
| Gate 1 (SDD) | 本テスト設計が SDD に含まれていること ✅ |
| Gate 3 (実装後) | 単体テスト・結合テストが CI で全件 PASS すること |
| Gate 5 (QA実行) | E2Eテストが chromium / firefox / webkit 全てで PASS すること |
| Gate 6 (最終) | カバレッジ目標を達成していること |

---

### 10.6 カバレッジ目標

| 対象 | 目標 | 計測方法 |
|------|------|---------|
| 単体テスト ステートメントカバレッジ | **80%以上** | `vitest --coverage` |
| 新規追加（ProgressRing, getChannelIcon） | **100%** | 同上 |
| E2Eシナリオ対象コンポーネント | UI刷新対象5コンポーネント全て | Playwright レポート |

---

### 10.7 テスト実行手順

#### 単体・結合テスト

```bash
cd frontend
npm test                   # Vitest 単回実行
npm run test:watch         # watch モード
npx vitest --coverage      # カバレッジレポート付き
```

#### E2Eテスト（実装後）

```bash
# 事前: アプリをDockerで起動
docker compose up -d

# Playwright インストール（初回のみ）
cd frontend
npx playwright install

# E2Eテスト実行
npx playwright test                       # 全ブラウザ
npx playwright test --project=chromium   # Chrome のみ
npx playwright test --ui                 # UIモード（デバッグ用）
```

#### CI (GitHub Actions) 実行順

```
1. npm test              # 単体・結合テスト
2. npm run build         # ビルド確認
3. docker compose up -d  # E2E環境起動
4. npx playwright test   # E2Eテスト（全ブラウザ）
```

---

### 10.8 テスト対象外（スコープ外）

| 項目 | 理由 |
|------|------|
| CSS box-shadow の pixel-perfect 描画 | ブラウザ実装依存、スクリーンショットテストは不安定なため |
| アニメーション途中フレームの視覚確認 | 再現性が低い。開閉後の最終状態のみテスト |
| バックエンドAPIの結合テスト | バックエンドは別テストスイートで管理 |

---

### 10.9 追加機能テスト設計（スコープ拡張対応）

> **更新日**: 2026-03-22 / **対応**: ttoアップグレード要望 — AudioVisualizer・2カラム・歌詞カラオケ・曲名改善・バグ修正

#### 10.9.1 AudioVisualizer — Web Audio API + Canvas/WebGL

**前提**: Web Audio API / Canvas はブラウザAPIのため、Vitest（jsdom環境）ではグローバルモックが必須。

ファイル: `frontend/src/__tests__/AudioVisualizer.test.tsx`

| # | テストケース | 種別 | 詳細 |
|---|------------|------|------|
| U-49 | AudioContext生成 | 単体 | コンポーネントマウント時に `AudioContext` が生成される |
| U-50 | 非再生時の非表示 | 単体 | `isPlaying=false` の場合、Canvasビジュアライザーが表示されないこと |
| U-51 | 再生時の表示 | 単体 | `isPlaying=true` の場合、Canvas/SVG要素が存在すること |
| U-52 | アンマウント時クリーンアップ | 単体 | コンポーネントアンマウント時に `AudioContext.close()` が呼ばれること |
| U-53 | streamUrl変更時の再接続 | 単体 | `streamUrl` 変更時にAudio Sourceが再作成されること |
| I-06 | Player内Visualizer統合 | 結合 | PlayerにVisualizerが埋め込まれ、再生状態連動で表示/非表示が切り替わる |

**Vitestモック実装方針**（`vitest.setup.ts` に追加）:

```ts
vi.stubGlobal('AudioContext', vi.fn(() => ({
  createAnalyser: vi.fn(() => ({
    fftSize: 0,
    frequencyBinCount: 128,
    getByteFrequencyData: vi.fn(),
    connect: vi.fn(),
  })),
  createMediaElementSource: vi.fn(() => ({ connect: vi.fn() })),
  close: vi.fn(),
})));
```

**E2Eテスト**:

| # | テストケース | 検証方法 |
|---|------------|---------|
| E-18 | ビジュアライザー表示確認 | チャンネル選択・再生後に Canvas または SVG 要素が visible |
| E-19 | 停止時の非表示 | 停止ボタン押下後にビジュアライザーが非表示になること |
| E-20 | アニメーション更新確認 | 再生中に Canvas の描画またはCSSアニメーションが更新されていること |

---

#### 10.9.2 2カラムレイアウト — レスポンシブ左右分割

ファイル: `frontend/src/__tests__/integration/TwoColumnLayout.test.tsx`

| # | テストケース | 種別 | 詳細 |
|---|------------|------|------|
| U-54 | デスクトップ: 2カラム構造 | 単体 | 幅1024px時にメインコンテナが2列のグリッド/フレックスレイアウトを持つ |
| U-55 | モバイル: 1カラム構造 | 単体 | 幅640px未満で縦積み（1カラム）に変化すること |
| U-56 | 左カラム配置確認 | 単体 | 左カラムに ChannelSelector・Player・RequestForm・TrackHistory が配置されること |
| U-57 | 右カラム配置確認 | 単体 | 右カラムに MediaDisplay（AudioVisualizer + LyricsDisplay karaoke-overlay）が配置されること |
| I-07 | カラム間のstate共有 | 結合 | 左カラムのチャンネル選択が右カラムのNowPlayingに反映される |

**E2Eテスト**:

| # | テストケース | 検証方法 |
|---|------------|---------|
| E-21 | デスクトップ (1024px) 2列表示 | `getComputedStyle` でグリッド2列レイアウト確認 |
| E-22 | タブレット (768px) レイアウト確認 | ブレークポイント境界での崩れがないこと |
| E-23 | モバイル (767px) 1列への変化 | viewport 767px（< 768px境界）で縦積みに変化すること |
| E-24 | モバイル (320px) 最小幅 | 320pxで水平スクロールが発生しないこと |

---

#### 10.9.3 歌詞カラオケ表示 — 自動スクロール + ハイライト

ファイル: `frontend/src/__tests__/LyricsDisplay.test.tsx`（既存に追記）

| # | テストケース | 種別 | 詳細 |
|---|------------|------|------|
| U-58 | 現在行のハイライト | 単体 | `elapsedMs` に対応する行が `active` / `highlight` クラスを持つこと |
| U-59 | 前後行の非ハイライト | 単体 | 現在行以外の行がハイライトクラスを持たないこと |
| U-60 | 進捗0時の先頭行 | 単体 | `elapsedMs=0` で1行目がハイライトされること |
| U-61 | 進捗100%時の末尾行 | 単体 | `elapsedMs=durationMs` で最終行がハイライトされること |
| U-62 | 歌詞なし時の非表示 | 単体 | `lyrics=null` の場合、歌詞コンポーネントが表示されないこと |
| U-63 | スクロールマスクコンテナ存在 | 単体 | `overflow: hidden` のスクロールマスクコンテナが存在すること |
| I-08 | elapsedMs変化→ハイライト更新 | 結合 | `elapsedMs` props変化時に対応行のハイライトクラスが更新される |

**E2Eテスト**:

| # | テストケース | 検証方法 |
|---|------------|---------|
| E-25 | 歌詞ハイライト表示確認 | 歌詞ありトラック再生後、現在行が視覚的にハイライトされている |
| E-26 | 自動スクロール確認 | 時間経過（30秒後）に歌詞の `scrollTop` が変化していること |
| E-27 | スクロール後の歌詞可視性 | スクロール後も現在行が表示エリア内に収まっていること |

---

#### 10.9.4 曲名表示改善 — now-playing API連携

ファイル: `frontend/src/__tests__/Player.test.tsx`・`NowPlaying.test.tsx`（既存に追記）

| # | テストケース | 種別 | 詳細 |
|---|------------|------|------|
| U-64 | title優先表示 | 単体 | `nowPlaying.title` が存在する場合、`title` が `caption` より優先表示される |
| U-65 | caption フォールバック | 単体 | `nowPlaying.title` が undefined の場合、`caption` が表示される |
| U-66 | now-playing API polling | 単体 | 一定間隔（30秒など）で now-playing API が呼ばれること（`vi.useFakeTimers` 使用） |
| U-67 | API応答による自動更新 | 単体 | APIレスポンス変化時に表示中のトラック名が更新される |
| I-09 | チャンネル切替→APIリセット | 結合 | チャンネル選択変更時に now-playing pollingがリセット・再取得される |

---

#### 10.9.5 バグ修正回帰テスト — playlist_generator.py パス問題

**対象**: `backend/playlist_generator.py` のファイルパス生成ロジック

ファイル: `backend/tests/test_playlist_generator.py`（新規作成）

| # | テストケース | 種別 | 詳細 |
|---|------------|------|------|
| R-01 | 絶対パス生成 | 単体 (Python) | `playlist_generator` が絶対パスを生成すること（`os.path.abspath` または `pathlib.Path` 使用） |
| R-02 | 相対パス不使用 | 単体 (Python) | 生成パスが相対パス（`./` や `../` 始まり）でないこと |
| R-03 | ファイル不存在時のエラー | 単体 (Python) | 対象ファイルが存在しない場合に適切なエラーが発生すること |
| R-04 | Docker環境での動作確認 | 結合 (Python) | Docker Compose起動後にplaylist生成→ストリームURLが有効であること |
| R-05 | パス生成の再現性 | 単体 (Python) | 同じ入力に対して毎回同一のパスが生成されること |

**E2Eテスト（回帰）**:

| # | テストケース | 検証方法 |
|---|------------|---------|
| E-28 | ストリーム再生確認 | チャンネル選択後、ストリームURLへのHTTPリクエストが200を返すこと |
| E-29 | プレーヤー再生エラーなし | 再生後30秒間、ブラウザコンソールにメディアエラーが出ないこと |

---

### 10.10 更新後の合計テストケース数

| レイヤー | 元の件数 | 追加件数 | 合計 |
|---------|---------|---------|------|
| 単体テスト (U-xx) | 48件 | 19件 | **67件** |
| 結合テスト (I-xx) | 5件 | 4件 | **9件** |
| E2Eテスト (E-xx) | 17件 | 12件 | **29件** |
| 回帰テスト (R-xx) | 0件 | 5件 | **5件** |
| **合計** | **70件** | **40件** | **110件** |

### 10.11 追加機能に伴うカバレッジ目標更新

| 対象 | 目標 | 計測方法 |
|------|------|---------|
| `AudioVisualizer` コンポーネント（新規） | **100%** | `vitest --coverage` |
| `LyricsDisplay` カラオケ拡張部分 | **90%以上** | 同上 |
| `playlist_generator.py` パス生成関数 | **100%**（バグ修正箇所） | `pytest --cov` |
| フロントエンド全体（単体+結合） | **80%以上** | `vitest --coverage` |

### 10.12 Gate 3（実装）への申し送り事項

1. **Web Audio API モック設定**: `vitest.setup.ts` に `AudioContext` グローバルモックを追加すること
2. **Playwright 導入必須**: `@playwright/test` を `package.json` devDependencies に追加し、`playwright.config.ts`（`baseURL: http://localhost:3200`）を作成すること
3. **Python テスト環境整備**: `backend/` に `pytest` + `pytest-cov` を導入し、`test_playlist_generator.py` を作成すること
4. **CI更新**: GitHub Actions に Playwright E2E ステップ・Python pytest ステップを追加すること
5. **フェイクタイマー使用**: now-playing polling テスト（U-66）は `vi.useFakeTimers()` を使用すること

---

## 11. リスク評価・ロールバック方針

### 11.1 リスク評価

| # | リスク | 影響度 | 発生確率 | 対策 |
|---|--------|--------|---------|------|
| R-01 | ネオモーフィズムシャドウがブラウザ間で描画差異を生じる | 中 | 低 | 各ブラウザでE2E確認、差異が大きい場合は shadow 強度を弱める |
| R-02 | `backdrop-filter` の Safari 未対応バージョンで背景ぼかしが効かない | 低 | 低 | `-webkit-backdrop-filter` prefix を付与（SDD 3.1 済み）|
| R-03 | ProgressRing の SVG が低スペック端末でアニメーションが重くなる | 低 | 低 | `prefers-reduced-motion` 対応で無効化。`React.memo` でリレンダリング抑制 |
| R-04 | `max-height` アニメーションで歌詞が長い場合に切れる | 中 | 中 | `max-height: 500px` を採用。長歌詞は実データで確認し、必要なら値を拡大 |
| R-05 | 既存テストが新CSSクラス名の変更で壊れる | 高 | 中 | Gate 3 実装時に既存テストを先に更新してから実装する |

### 11.2 ロールバック方針

Phase 1 は専用フィーチャーブランチで実装し、`main` への直接プッシュは禁止とする。

#### 手順

1. **PRクローズ（マージ前）**: PRをクローズするだけでロールバック完了。`main` は汚染されない。
2. **マージ後の部分ロールバック**: 特定コンポーネントのみ戻す場合、対象ファイルを `git revert` または元コードに差し戻す。
3. **完全ロールバック**: マージコミットを `git revert <merge-commit-sha>` で一括取り消し。

```bash
# マージコミット特定
git log --oneline -5

# マージ全体をロールバック（-m 1 = mainラインを基準）
git revert -m 1 <merge-commit-sha>
git push origin main
```

#### ロールバック判断基準

| 状況 | 対応 |
|------|------|
| E2Eテストが1ブラウザで FAIL | 修正を優先。ロールバックは最終手段 |
| 本番（Docker Compose）で起動不能 | 即時 PRクローズ または `git revert` |
| パフォーマンス指標が著しく悪化（Lighthouse -20点以上） | PRクローズ後に原因特定・修正してから再提出 |

---

## 10. バグ修正設計: playlist_generator.py パス問題

> **担当**: System Engineer
> **優先度**: High — ホスト/コンテナ間のパス不一致により Liquidsoap がトラックを再生できない

---

### 10.1 問題の特定

**症状**: Liquidsoap がプレイリストを読み込んでもトラックを再生できない（silence にフォールバックし続ける）

**根本原因**: `playlist_generator.py` が M3U エントリにホスト側パスを書き込んでいるが、Liquidsoap はコンテナ内パスで読む必要がある。

#### パス対応関係

| 場所 | パス |
|------|------|
| ホスト（Worker実行環境） | `./generated_tracks/{slug}/{uuid}.flac` |
| Liquidsoap コンテナ内 | `/tracks/{slug}/{uuid}.flac` |
| Docker volume mount | `./generated_tracks:/tracks` |

#### コード調査結果

`worker/config.py`:
```python
generated_tracks_dir: str = "./generated_tracks"  # ホスト側パス
```

`worker/playlist_generator.py` (問題箇所 L45-51):
```python
base_dir = Path(tracks_dir)         # = ./generated_tracks (ホスト)
for track in tracks:
    full_path = base_dir / track.file_path   # = ./generated_tracks/lofi/uuid.flac
    if not full_path.exists():
        continue
    weighted_entries.extend([str(full_path)] * weight)  # ← ホストパスを書き込む ❌
```

M3U に書き込まれるエントリ（現状）:
```
generated_tracks/lofi/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx.flac
```

Liquidsoap が期待するエントリ:
```
/tracks/lofi/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx.flac
```

---

### 10.2 修正設計

#### 方針: `liquidsoap_tracks_dir` パラメータを追加

ファイル存在チェック（ホスト側）と M3U エントリ書き込み（コンテナ側）を分離する。

**修正対象ファイル:**

| ファイル | 変更内容 |
|---------|---------|
| `worker/config.py` | `liquidsoap_tracks_dir` 設定を追加 |
| `worker/playlist_generator.py` | `playlist_tracks_dir` パラメータ追加、エントリ生成を分離 |
| `worker/queue_consumer.py` | `generate_weighted_playlist` 呼び出しに `playlist_tracks_dir` 追加 |
| `worker/auto_generator.py` | 同上 |

#### `worker/config.py` 変更仕様

```python
# 追加
liquidsoap_tracks_dir: str = "/tracks"  # Liquidsoap コンテナ内パス
```

#### `worker/playlist_generator.py` 変更仕様

```python
async def generate_weighted_playlist(
    session: AsyncSession,
    channel_id,
    channel_slug: str,
    tracks_dir: str,
    playlist_tracks_dir: str | None = None,  # 追加: Liquidsoap から見えるパス
) -> int:
    ...
    base_dir = Path(tracks_dir)
    # M3U エントリ用ベースパス（指定なければ tracks_dir と同じ — テスト互換）
    playlist_base = Path(playlist_tracks_dir) if playlist_tracks_dir else base_dir

    for track in tracks:
        host_path = base_dir / track.file_path        # ファイル存在チェック用（ホスト側）
        container_path = playlist_base / track.file_path  # M3U エントリ用（コンテナ側）
        if not host_path.exists():
            continue
        weight = max(1, track.like_count)
        weighted_entries.extend([str(container_path)] * weight)  # ← コンテナパスを書き込む ✅
```

#### `worker/queue_consumer.py` 変更仕様

```python
await generate_weighted_playlist(
    session, ch.id, ch.slug,
    str(self.tracks_dir),
    playlist_tracks_dir=settings.liquidsoap_tracks_dir,  # 追加
)
```

#### `worker/auto_generator.py` 変更仕様

```python
await generate_weighted_playlist(
    session, channel.id, channel.slug,
    settings.generated_tracks_dir,
    playlist_tracks_dir=settings.liquidsoap_tracks_dir,  # 追加
)
```

---

### 10.3 後方互換性・テスト影響

| 項目 | 影響 |
|------|------|
| 既存テスト (`test_playlist_generator.py`) | `playlist_tracks_dir` を省略すれば従来動作。**テスト変更不要** |
| ローカル開発（Dockerなし） | `LIQUIDSOAP_TRACKS_DIR=./generated_tracks` を `.env` に設定すれば同じパスを使用できる |
| 本番 Docker Compose 環境 | Worker の `.env` に `LIQUIDSOAP_TRACKS_DIR=/tracks` を追加するだけで修正完了 |

#### docker-compose.yml worker サービス 環境変数確認（推奨-5）

実装時に `docker-compose.yml` の `worker` サービスに以下の環境変数が設定されていることを確認すること:

```yaml
# docker-compose.yml（確認・追加箇所）
services:
  worker:
    environment:
      - LIQUIDSOAP_TRACKS_DIR=/tracks   # Liquidsoap コンテナ内パス（FR-110修正に必須）
    volumes:
      - ./generated_tracks:/tracks       # ホスト↔Liquidsoapコンテナ共有ボリューム（既存）
```

> **確認事項**: `./generated_tracks:/tracks` のボリュームマウントが `liquidsoap` サービスにも同様に設定されていること。Worker と Liquidsoap が同一ボリュームを共有していない場合はマウント設定を追加する。

---

### 10.4 修正の検証方法

```bash
# Docker Compose 起動後、プレイリストの内容を確認
cat generated_tracks/lofi/playlist.m3u
# 期待値: /tracks/lofi/xxxxxxxx.flac
# 修正前: generated_tracks/lofi/xxxxxxxx.flac または絶対ホストパス

# Liquidsoap コンテナ内からファイルの存在を確認
docker compose exec liquidsoap ls /tracks/lofi/
```

---

## 11. 技術設計: Web Audio API ビジュアライザー連携

> **担当**: System Engineer
> **対象**: `Player.tsx` の `VisualizerBars` を CSS アニメーションから Web Audio API 解析ベースに変更する際の技術的実現可能性と設計

---

### 11.1 現状のビジュアライザー実装

`Player.tsx` の `VisualizerBars` は現在 CSS アニメーション（`visualizer-bounce`）のみ。
再生中かどうかの boolean (`playing`) で表示/非表示を切り替えているのみで、**実際の音声データは使用していない**。

```tsx
function VisualizerBars({ playing }: { playing: boolean }) {
  if (!playing) return null;
  // CSS animation only — 実際の音声レベルとは無関係
  ...
}
```

---

### 11.2 既存のストリーミング方式との連携可否

#### ストリーミング構成

```
Liquidsoap → Icecast2 → Caddy → ブラウザ
             (OGG/Vorbis, HTTP)  <audio src="/stream/{slug}.ogg" />
```

#### Web Audio API 接続方式: MediaElementAudioSourceNode

`<audio>` 要素を `AudioContext` に接続する方式が最適:

```
<audio ref> → createMediaElementSource() → AnalyserNode → destination
```

**Icecast の CORS 設定**: `icecast.xml` にて `Access-Control-Allow-Origin: *` が設定済み ✅

---

### 11.3 実装設計

#### 制約事項

| 制約 | 内容 |
|------|------|
| ユーザーインタラクション必須 | `AudioContext` は再生ボタンクリック後に生成する（ブラウザ autoplay policy） |
| `createMediaElementSource` は1回のみ | 同一 `<audio>` 要素に対して複数回呼ぶと例外。`useRef` でガード必須 |
| `crossOrigin="anonymous"` が必要 | Web Audio API がクロスオリジンストリームを処理するために `<audio>` 要素に属性が必要（Safari 含む） |
| URL変更時の再接続不要 | `streamUrl` が変わっても `MediaElementAudioSourceNode` は既存のまま使用可能 |

#### `Player.tsx` 変更仕様

```tsx
// 追加する Refs
const audioContextRef = useRef<AudioContext | null>(null);
const analyserRef = useRef<AnalyserNode | null>(null);
const sourceRef = useRef<MediaElementAudioSourceNode | null>(null);
const animFrameRef = useRef<number | null>(null);
const [freqData, setFreqData] = useState<Uint8Array | null>(null);

// AudioContext の初期化（再生開始時に1回だけ実行）
function initAudioContext() {
  if (!audioRef.current || audioContextRef.current) return;
  // Safari フォールバック（FR-106-6）
  const AudioCtx = window.AudioContext ?? (window as Window & { webkitAudioContext?: typeof AudioContext }).webkitAudioContext;
  if (!AudioCtx) return;  // Web Audio API 未対応ブラウザではビジュアライザーをスキップ
  const ctx = new AudioCtx();
  const analyser = ctx.createAnalyser();
  analyser.fftSize = 64;  // 低解像度で十分（バー5本分）
  const source = ctx.createMediaElementSource(audioRef.current);
  source.connect(analyser);
  analyser.connect(ctx.destination);
  audioContextRef.current = ctx;
  analyserRef.current = analyser;
  sourceRef.current = source;
}

// アニメーションループ
function startVisualizerLoop() {
  const analyser = analyserRef.current;
  if (!analyser) return;
  const data = new Uint8Array(analyser.frequencyBinCount);
  const loop = () => {
    analyser.getByteFrequencyData(data);
    setFreqData(new Uint8Array(data));
    animFrameRef.current = requestAnimationFrame(loop);
  };
  animFrameRef.current = requestAnimationFrame(loop);
}

// togglePlay への追加
const togglePlay = () => {
  if (!audioRef.current || !streamUrl) return;
  if (isPlaying) {
    audioRef.current.pause();
    if (animFrameRef.current) cancelAnimationFrame(animFrameRef.current);
    setIsPlaying(false);
  } else {
    initAudioContext();  // 追加
    audioRef.current.play().catch(() => setIsPlaying(false));
    startVisualizerLoop();  // 追加
    setIsPlaying(true);
  }
};

// <audio> 要素に crossOrigin 追加（必須）
<audio ref={audioRef} src={streamUrl ?? undefined} preload="none" crossOrigin="anonymous" />
```

#### `VisualizerBars` の更新仕様

```tsx
// freqData がある場合は実データ、なければ CSS アニメーションにフォールバック
function VisualizerBars({
  playing,
  freqData,
}: {
  playing: boolean;
  freqData: Uint8Array | null;
}) {
  if (!playing) return null;
  const bars = Array.from({ length: 5 }, (_, i) => i);

  return (
    <div className="visualizer">
      {bars.map((i) => {
        // freqData がある場合: 周波数バンドから高さを計算
        // freqData がない場合: CSS アニメーションにフォールバック
        const height = freqData
          ? `${Math.max(15, (freqData[i * 4] / 255) * 100)}%`
          : undefined;
        return (
          <div
            key={i}
            className={`visualizer-bar ${freqData ? "" : "visualizer-bounce"}`}
            style={{
              height,
              animationDelay: freqData ? undefined : `${i * 0.15}s`,
              ["--duration" as string]: freqData ? undefined : `${0.6 + i * 0.1}s`,
            }}
          />
        );
      })}
    </div>
  );
}
```

---

### 11.4 CSS 変更仕様

Web Audio API ベースのバーは高さを JS で動的制御するため、CSS アニメーションと共存できるよう分離:

```css
/* 既存: CSS アニメーション版（フォールバック） */
.visualizer-bar {
  width: 3px;
  min-height: 4px;
  border-radius: 2px;
  background: var(--accent-primary);
  /* visualizer-bounce クラスが付いている場合のみアニメーション */
}

.visualizer-bounce {
  animation: visualizer-bounce var(--duration, 0.8s) ease-in-out infinite alternate;
}

/* 追加: Web Audio API 版（高さを JS で制御） */
.visualizer-bar-live {
  transition: height 80ms ease-out;  /* 滑らかな更新 */
}
```

---

### 11.5 パフォーマンス考慮事項

| 項目 | 内容 |
|------|------|
| `fftSize = 64` | バー5本に対して十分な解像度。最小 FFT サイズで CPU 負荷を最小化 |
| `setFreqData` の更新頻度 | `requestAnimationFrame`（約60fps）。`React.memo` で `VisualizerBars` の不要な再レンダリングを抑制推奨 |
| メモリリーク防止 | コンポーネントのアンマウント時 `cancelAnimationFrame` + `AudioContext.close()` を `useEffect` の cleanup で実行 |
| Safari 対応 | `crossOrigin="anonymous"` を `src` より先に設定（属性順序の問題を避けるため JSX では常に先頭に記述） |

---

### 11.6 変更対象ファイル（Web Audio API 設計）

| ファイル | 変更内容 |
|---------|---------|
| `frontend/src/components/Player.tsx` | AudioContext 初期化、AnalyserNode ループ、crossOrigin 属性追加、VisualizerBars 更新 |
| `frontend/src/styles.css` | `.visualizer-bounce` クラス分離、`.visualizer-bar-live` 追加 |

---

## 12. DBスキーマ設計: `tracks.video_url` カラム追加（将来フェーズ）

> **担当**: System Engineer
> **Phase**: 将来フェーズ（スキーマのみ先行追加）
> **方針**: Phase 1 では実データを投入しないが、DBカラムとモデル定義のみ先行追加する

---

### 12.1 設計概要

#### 追加カラム仕様

| テーブル | カラム名 | 型 | Nullable | デフォルト | 用途 |
|---------|---------|---|---------|-----------|------|
| `tracks` | `video_url` | `TEXT` | `NULL` | `NULL` | 動画コンテンツURL（将来フェーズで使用）|

#### 設計方針

- `TEXT` 型（URLの長さ制限なし）
- `NULL` 許容（Phase 1 では未入力のまま）
- インデックス不要（ルックアップ用途は将来検討）

---

### 12.2 Alembic マイグレーション設計

**ファイル**: `alembic/versions/004_add_video_url.py`

```python
"""tracks テーブルに video_url カラムを追加（将来フェーズ用）

Revision ID: 004
Revises: 003
Create Date: 2026-03-22

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "004"
down_revision: str | None = "003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "tracks",
        sa.Column("video_url", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("tracks", "video_url")
```

---

### 12.3 SQLAlchemy モデル変更

**ファイル**: `worker/models.py` — `Track` クラスへの追加

```python
# 既存カラムの後（created_at の前）に追加
video_url: Mapped[Optional[str]] = mapped_column(Text)
```

追加箇所（既存コードとの整合性）:

```python
class Track(Base):
    __tablename__ = "tracks"
    # ... 既存フィールド ...
    is_retired: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    last_played_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    video_url: Mapped[Optional[str]] = mapped_column(Text)  # 追加
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
```

---

### 12.4 Pydantic スキーマ変更

**ファイル**: `api/schemas.py` — `TrackResponse` への追加

```python
class TrackResponse(BaseModel):
    id: uuid.UUID
    title: str | None = None
    caption: str
    mood: str | None = None
    lyrics: str | None = None
    duration_ms: int | None = None
    bpm: int | None = None
    music_key: str | None = None
    instrumental: bool | None = None
    play_count: int = 0
    like_count: int = 0
    video_url: str | None = None  # 追加（Phase 1 では常に null）
    created_at: datetime
```

---

### 12.5 フロントエンド型定義変更

**ファイル**: `frontend/src/api/types.ts` — `Track` インターフェースへの追加

```typescript
export interface Track {
  id: string;
  caption: string;
  title?: string;
  mood?: string;
  lyrics?: string;
  duration_ms: number | null;
  bpm: number | null;
  music_key: string | null;
  instrumental: boolean | null;
  play_count: number;
  like_count: number;
  video_url?: string | null;  // 追加（Phase 1 では null）
  created_at: string;
}
```

---

### 12.6 変更対象ファイル一覧

| ファイル | 変更内容 | 優先度 |
|---------|---------|--------|
| `alembic/versions/004_add_video_url.py` | **新規作成**: video_url カラム追加マイグレーション | 将来フェーズ |
| `worker/models.py` | `Track.video_url` フィールド追加 | 将来フェーズ |
| `api/schemas.py` | `TrackResponse.video_url` フィールド追加 | 将来フェーズ |
| `frontend/src/api/types.ts` | `Track.video_url` 型定義追加 | 将来フェーズ |

> **注意**: Phase 1 の実装スコープには含まない。将来フェーズのPR作成時に合わせてマイグレーション適用すること。

---

## 13. API設計: 歌詞タイミング推定（Phase 1）と将来フェーズ設計

> **担当**: System Engineer

---

### 13.1 Phase 1: フロントエンド推定（実装済み）

`LyricsDisplay.tsx` に既に実装済み:

```typescript
// LyricsDisplay.tsx (L47-50) — 現在の推定ロジック
const progress = durationMs > 0 ? Math.min(elapsedMs / durationMs, 1) : 0;
const currentLineIndex = Math.floor(progress * totalLines);
// → 楽曲長を歌詞行数で等分割してハイライト位置を推定
```

**Phase 1 推定方式の評価**:

| 項目 | 内容 |
|------|------|
| アルゴリズム | `elapsedMs / durationMs × totalLines` で現在行を推定 |
| 精度 | 中精度（イントロ・アウトロ・間奏を考慮しない） |
| 実装コスト | 0（既に実装済み） |
| バックエンド変更 | 不要 |
| 問題点 | 無音部分やリフレイン繰り返しで行がズレる |

Phase 1 ではこの推定をそのまま維持する。変更なし。

---

### 13.2 将来フェーズ: タイムスタンプ付き歌詞データAPI設計

#### データ形式

**選択形式: LRC（Lyric Rich Container）形式** — デファクトスタンダード

```
[00:00.00]♪ 音楽イントロ
[00:08.50]花びらが舞う 夜に
[00:12.30]風が語りかける
[00:16.80][Chorus]
[00:17.00]空を越えて 届け
[00:21.40]この想い
```

**代替形式: JSON構造（API用）**

```json
{
  "timing": [
    {"time_ms": 0,     "text": "♪ 音楽イントロ"},
    {"time_ms": 8500,  "text": "花びらが舞う 夜に"},
    {"time_ms": 12300, "text": "風が語りかける"},
    {"time_ms": 16800, "text": "[Chorus]"},
    {"time_ms": 17000, "text": "空を越えて 届け"},
    {"time_ms": 21400, "text": "この想い"}
  ]
}
```

#### DBスキーマ追加（将来フェーズ）

`tracks` テーブルに `lyrics_timing` カラムを追加:

| カラム名 | 型 | Nullable | 用途 |
|---------|---|---------|------|
| `lyrics_timing` | `JSONB` | `NULL` | タイムスタンプ付き歌詞（将来フェーズ） |

マイグレーション（将来フェーズ `005_lyrics_timing.py` に含める）:

```python
def upgrade() -> None:
    op.add_column(
        "tracks",
        sa.Column(
            "lyrics_timing",
            sa.dialects.postgresql.JSONB(),
            nullable=True,
        ),
    )
    # 高速検索は不要のためインデックスなし
```

#### 将来APIエンドポイント設計

**方式A: `TrackResponse` に含める（推奨）**

```python
# api/schemas.py — 将来フェーズ追加
class LyricsTiming(BaseModel):
    time_ms: int
    text: str

class TrackResponse(BaseModel):
    # ... 既存フィールド ...
    lyrics_timing: list[LyricsTiming] | None = None  # 将来追加
```

`GET /api/channels/{slug}/now-playing` → `TrackResponse.lyrics_timing` を含めて返す。
フロントエンドは `lyrics_timing` がある場合はタイムスタンプ使用、ない場合は推定方式にフォールバック。

**方式B: 専用エンドポイント（オプション）**

```
GET /api/tracks/{track_id}/lyrics-timing
→ { timing: [{ time_ms: int, text: string }] }
```

容量が大きい場合や on-demand 取得が必要な場合に採用。Phase 1 では不要。

#### フロントエンド実装方針（将来フェーズ）

```typescript
// LyricsDisplay.tsx — 将来フェーズの拡張
interface LyricLine {
  time_ms: number;
  text: string;
}

// lyrics_timing がある場合: 正確なタイムスタンプで現在行を特定
const currentLine = lyricsTiming
  ? lyricsTiming.findLast((l) => l.time_ms <= elapsedMs)
  : undefined;

// ない場合: 既存の推定ロジックにフォールバック
const progress = durationMs > 0 ? Math.min(elapsedMs / durationMs, 1) : 0;
const estimatedLineIndex = Math.floor(progress * totalLines);
```

---

### 13.3 フェーズ別ロードマップ

| フェーズ | 内容 | 状態 |
|---------|------|------|
| Phase 1 (現行) | `elapsedMs / durationMs × 行数` 推定。既実装 | ✅ 実装済み（変更不要） |
| 将来フェーズ A | `tracks.lyrics_timing JSONB` カラム追加 + `TrackResponse` 拡張 | 設計済み（実装は将来） |
| 将来フェーズ B | ACE-Step 音声解析から自動タイミング抽出、または LRC 手動入力 | 未設計 |

---

### 13.4 変更対象ファイル一覧（将来フェーズ分）

| ファイル | 変更内容 | フェーズ |
|---------|---------|---------|
| `alembic/versions/005_lyrics_timing.py` | `lyrics_timing JSONB` カラム追加マイグレーション | 将来 |
| `worker/models.py` | `Track.lyrics_timing` フィールド追加 | 将来 |
| `api/schemas.py` | `LyricsTiming` モデル追加、`TrackResponse` 拡張 | 将来 |
| `frontend/src/api/types.ts` | `Track.lyrics_timing` 型定義追加 | 将来 |
| `frontend/src/components/LyricsDisplay.tsx` | タイムスタンプ優先 + 推定フォールバック | 将来 |
