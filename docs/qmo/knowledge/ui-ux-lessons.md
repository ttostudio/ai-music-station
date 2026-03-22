# UI/UX設計ナレッジ — AI Music Station

> **蓄積日**: 2026-03-22
> **対象フェーズ**: Phase 1 UI刷新（Issue #347）
> **担当**: Designer

---

## 1. モバイル対応ナレッジ

### 1.1 2カラム → 1カラム レスポンシブ切り替え

**教訓**: デスクトップ2カラム（左: 操作パネル / 右: メディア全面）は、768px 未満で1カラムスタックに切り替える。

```css
@media (max-width: 767px) {
  .app-layout { grid-template-columns: 1fr; }
  .left-column, .right-column { max-height: none; position: static; }
  .right-column .media-display { height: 240px; }
}
```

**ビジュアライザー配置**: モバイルでは高さを `240px` に縮小し、Player 直下に配置。フルスクリーン背景は操作性を損なうため採用しない。

---

### 1.2 タッチ操作性の確保

**教訓**: タッチターゲットは最小 **44〜48px** を守る（Apple HIG / Google MDC 基準）。

| 要素 | 推奨サイズ | 実装 |
|------|-----------|------|
| チャンネルカード | min-height: 48px | `--card-channel-height: 140px` で十分 |
| 再生/停止ボタン | min 64px | 72px SVGリング（`--ring-size`）が条件を満たす |
| いいねボタン | padding で拡張 | `padding: 0.75rem` で視覚より広いタップ領域 |

```css
/* タッチデバイスではホバーエフェクトを無効化 */
@media (hover: hover) {
  .channel-card:hover { transform: translateY(-4px); }
}
/* :active は全デバイスで有効 */
.channel-card:active { transform: scale(0.97); }
/* 全操作要素に付与 */
button, [role="button"] { touch-action: manipulation; }
```

---

### 1.3 スワイプでチャンネル切り替え

```tsx
const startX = useRef(0);
const MIN_SWIPE_PX = 60;

const handleTouchStart = (e: React.TouchEvent) => {
  startX.current = e.touches[0].clientX;
};
const handleTouchEnd = (e: React.TouchEvent) => {
  const diff = startX.current - e.changedTouches[0].clientX;
  if (Math.abs(diff) > MIN_SWIPE_PX) {
    diff > 0 ? selectNextChannel() : selectPrevChannel();
  }
};
```

**注意**: コンテナに `touch-action: pan-y` を設定してブラウザの縦スクロールを妨げない。

---

### 1.4 iOS Safari オーディオ自動再生制限

**原則**: `play()` はユーザーインタラクション（タップ）ハンドラ内からのみ呼ぶ。`setTimeout` や `useEffect` からの自動呼び出しは iOS Safari で `NotAllowedError` になる。

```tsx
const togglePlay = async () => {
  try {
    await audioRef.current?.play();
    setIsPlaying(true);
  } catch (err) {
    if ((err as DOMException).name === 'NotAllowedError') {
      setShowPlayPrompt(true); // 「タップして再生」UIを表示
    }
    setIsPlaying(false);
  }
};
```

**Web Audio API**: iOS Safari では `AudioContext` が `suspended` 状態で始まる。`ctx.resume()` をユーザー操作内で呼ぶ必要がある。

```ts
const initAudioContext = async () => {
  if (!audioCtxRef.current) {
    audioCtxRef.current = new AudioContext();
  }
  if (audioCtxRef.current.state === 'suspended') {
    await audioCtxRef.current.resume();
  }
};
// → 再生ボタン押下時（ユーザーインタラクション内）でのみ呼ぶ
```

---

### 1.5 バックグラウンド再生 — Media Session API

```ts
useEffect(() => {
  if (!('mediaSession' in navigator) || !nowPlaying) return;

  navigator.mediaSession.metadata = new MediaMetadata({
    title: nowPlaying.title || nowPlaying.caption || '再生中',
    artist: 'AI Music Station',
    album: activeChannel?.name ?? '',
  });

  navigator.mediaSession.setActionHandler('play',  () => audioRef.current?.play());
  navigator.mediaSession.setActionHandler('pause', () => audioRef.current?.pause());

  return () => {
    navigator.mediaSession.setActionHandler('play', null);
    navigator.mediaSession.setActionHandler('pause', null);
  };
}, [nowPlaying, activeChannel]);
```

**対応ブラウザ**: Chrome 73+, Safari 15+, Firefox 82+。未対応は graceful degradation。

---

### 1.6 リクエストフォーム — キーボード表示時のレイアウト崩れ防止

```css
/* iOS 15.4+ Safari: Dynamic Viewport Height でキーボード縮小に対応 */
@supports (height: 100dvh) {
  .left-column { max-height: calc(100dvh - 4rem); }
}
```

```tsx
// 入力フィールドフォーカス時に画面内にスクロール
const handleFocus = (e: React.FocusEvent) => {
  setTimeout(() => {
    e.target.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
  }, 300); // キーボードアニメーション完了後
};
```

---

### 1.7 低速回線での読み込み最適化

| 対策 | 内容 |
|------|------|
| `<audio preload="none">` | 選択前にオーディオを読み込まない |
| `AudioContext` 遅延初期化 | 再生ボタン押下時のみ生成 |
| Canvas 描画の停止 | 停止中は `cancelAnimationFrame` で CPU 削減 |
| 画像レス設計 | アートワーク画像なし（絵文字アイコン使用）|

---

## 2. レイヤー設計ナレッジ — MediaDisplay + オーバーレイ

### 2.1 ビジュアライザー上への歌詞オーバーレイ

**基本パターン**: `position: relative` コンテナ + 子要素を `position: absolute; inset: 0; z-index` で重ねる。

```css
.media-display { position: relative; overflow: hidden; }
.viz-canvas, .media-video { position: absolute; inset: 0; z-index: 0; }
.karaoke-overlay { position: absolute; inset: 0; z-index: 10; pointer-events: none; }
```

### 2.2 歌詞の可読性確保（背景映像との差別化）

優先度順:

1. **テキストシャドウ（軽量・全ライン）**:
   `text-shadow: 0 1px 4px rgba(0,0,0,0.9), 0 0 8px rgba(0,0,0,0.7)`
2. **半透明背景帯（アクティブ行のみ）**:
   `background: rgba(0,0,0,0.45); backdrop-filter: blur(4px)`
3. フルオーバーレイ（コントラスト強すぎで NG）

### 2.3 MediaDisplay 拡張性設計

**教訓**: 将来機能は optional props で吸収する。フィーチャーフラグより型安全でシンプル。

```tsx
interface MediaDisplayProps {
  videoUrl?: string; // Phase 1: 常に undefined → Phase 2: 動画URL
  audioRef: React.RefObject<HTMLAudioElement>;
  isPlaying: boolean;
  channelSlug: string | null;
  lyrics?: string | null;
  elapsedMs: number;
  durationMs: number;
}
```

---

## 3. カラオケ歌詞表示ナレッジ

### 3.1 ライン状態の色分け

| 状態 | opacity | font-size | 備考 |
|------|---------|-----------|------|
| 過去行（2行以上前） | 0.25 | 0.85rem | 存在感を最小化 |
| 過去行（直前1行） | 0.4 | 0.95rem | 文脈の繋がり |
| **現在行** | 1.0 | 1.15rem | グラデーション+glow |
| 未来行（直後1行） | 0.75 | 1.0rem | 次のラインを予見 |
| 未来行（2行以降） | 0.5 | 0.9rem | 控えめに表示 |

### 3.2 自動スクロール実装

```tsx
useEffect(() => {
  const prefersReducedMotion =
    window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  activeLineRef.current?.scrollIntoView({
    behavior: prefersReducedMotion ? 'instant' : 'smooth',
    block: 'center',
  });
}, [activeIndex]);
```

### 3.3 ライン進捗の計算（タイムスタンプなし版）

```ts
// Phase 1: 均等分割推定
const lines = lyrics.split('\n').filter(l => l.trim());
const activeIndex = Math.floor((elapsedMs / durationMs) * lines.length);

// Phase 2以降: LRC形式のタイムスタンプがあれば正確なマッピングが可能
// [00:12.34] ライン → { time: 12340, text: 'ライン' }
```

---

## 4. PWA化の検討事項（Phase 2以降）

```json
{
  "name": "AI Music Station",
  "short_name": "AIミュージック",
  "theme_color": "#0a0a0f",
  "background_color": "#0a0a0f",
  "display": "standalone",
  "start_url": "/"
}
```

**注意**:
- オーディオストリームは Service Worker でキャッシュしない（ライブストリーム不可）
- UIアセット（JS/CSS/HTML）のみキャッシュ対象
- iOS Safari PWA はバックグラウンド再生が制限される場合がある

---

*このファイルは AI Music Station の UI/UX 設計から得られたナレッジを蓄積するものです。今後のフェーズや類似プロダクト開発時の参考として活用してください。*
