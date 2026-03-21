# AI Music Station — Phase 1 設計書 (SDD)

## 概要

ラジオ体験を「AIが作曲・歌唱し、リスナーがフィードバックで育てる」システムに進化させる。
ユーザーは「雰囲気」を一言伝えるだけで、歌詞・曲名が自動生成され、ボーカル付き楽曲がストリーミングされる。

## 機能一覧

| # | 機能 | 概要 |
|---|------|------|
| F1 | 歌詞・曲名の自動生成 | 雰囲気 → Claude API で歌詞/曲名生成 → ACE-Step でボーカル付き生成 |
| F2 | 楽曲情報表示 | 再生中の曲名・歌詞をWebで表示（カラオケ風スクロール） |
| F3 | フィードバックシステム | 👍スタンプ → 好み分析 → 次回生成に反映 |
| F4 | チャンネル自動生成 | 雰囲気設定 + システムリソース監視 + バックグラウンド自動生成 |
| F5 | ラジオ再生改善 | 不人気曲の棚卸し + 👍重み付きシャッフル |
| F6 | ANTHROPIC_API_KEY管理 | サーバーサイド環境変数のみ、フロント不要 |

## アーキテクチャ

```
ユーザー → Web UI (React)
  ↓ POST /api/channels/{slug}/requests { mood: "アップテンポなアニソン" }
  ↓
FastAPI → Claude API（歌詞・曲名生成）
  ↓ { title, lyrics, caption }
  ↓ INSERT requests + track_metadata
  ↓
Worker → ACE-Step（音楽生成）
  ↓ FLAC ファイル保存
  ↓
Liquidsoap → Icecast → ブラウザ <audio>
  ↓ now-playing webhook
  ↓
Web UI ← 曲名・歌詞・👍ボタン表示
```

---

## F1: 歌詞・曲名の自動生成

### 設計方針
- リクエスト時に `mood`（雰囲気）パラメータを追加
- `mood` が指定された場合、API側で Claude API を呼び出し歌詞と曲名を生成
- 生成結果を `requests` テーブルに保存し、Worker に渡す
- `caption` と `lyrics` を直接指定した場合は Claude API をスキップ

### Claude API プロンプト設計

```
あなたは音楽の作詞家です。以下の雰囲気に合った楽曲を作成してください。

チャンネル: {channel_name}
雰囲気: {mood}

以下のJSON形式で回答してください:
{
  "title": "曲名（日本語）",
  "caption": "ACE-Step用の英語キャプション（ジャンル、楽器、雰囲気を含む）",
  "lyrics": "[Verse 1]\n歌詞...\n\n[Chorus]\n歌詞...\n\n[Verse 2]\n歌詞...\n\n[Chorus]\n歌詞..."
}
```

### 新サービス: `worker/lyrics_generator.py`

```python
class LyricsGenerator:
    def __init__(self, api_key: str):
        self.client = anthropic.Anthropic(api_key=api_key)

    async def generate(self, mood: str, channel: Channel) -> LyricsResult:
        # Claude API呼び出し
        # → LyricsResult(title, caption, lyrics)
```

### APIフロー変更

```
POST /api/channels/{slug}/requests
  Body: { mood?: str, caption?: str, lyrics?: str, ... }

  if mood:
    lyrics_result = await lyrics_generator.generate(mood, channel)
    # title, caption, lyrics を自動設定
  else:
    # 従来通り caption/lyrics を直接使用
```

### DBスキーマ変更

```sql
ALTER TABLE requests ADD COLUMN mood TEXT;
ALTER TABLE tracks ADD COLUMN title TEXT;
ALTER TABLE tracks ADD COLUMN mood TEXT;
```

### 環境変数

```
ANTHROPIC_API_KEY=sk-ant-...  # サーバーサイドのみ
```

---

## F2: 楽曲情報表示

### now_playing の拡張

現在の `now_playing` レスポンスに `title` と `lyrics` を追加:

```json
GET /api/channels/{slug}/now-playing
{
  "track": {
    "id": "...",
    "title": "夜明けのメロディ",
    "caption": "anime opening theme...",
    "lyrics": "[Verse 1]\n朝焼けの空に...\n\n[Chorus]\n走り出せ...",
    "duration_ms": 90000,
    "bpm": 140,
    "music_key": "C",
    "instrumental": false,
    "play_count": 3,
    "created_at": "..."
  }
}
```

### フロントエンド: LyricsDisplay コンポーネント

```
<LyricsDisplay lyrics={track.lyrics} />
```

- 歌詞をセクション（[Verse], [Chorus]等）ごとにパース
- 現在の再生位置に応じてスクロール（推定位置 = 経過時間 / 楽曲長 × 歌詞全体）
- カラオケ風ハイライト（CSSアニメーション）

### フロントエンド: TrackTitle コンポーネント

```
<TrackTitle title={track.title} mood={track.mood} />
```

---

## F3: フィードバックシステム

### 新テーブル: `reactions`

```sql
CREATE TABLE reactions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  track_id UUID NOT NULL REFERENCES tracks(id),
  session_id VARCHAR(100) NOT NULL,  -- ブラウザセッションID
  reaction_type VARCHAR(20) NOT NULL DEFAULT 'like',  -- 'like'
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE (track_id, session_id)  -- 同一セッションからの重複防止
);
CREATE INDEX idx_reactions_track ON reactions(track_id);
```

### APIエンドポイント

```
POST /api/tracks/{track_id}/reactions
  Body: { session_id: str, reaction_type: "like" }
  Response: { ok: true, count: 5 }

DELETE /api/tracks/{track_id}/reactions
  Body: { session_id: str }
  Response: { ok: true, count: 4 }

GET /api/tracks/{track_id}/reactions
  Response: { count: 5, user_reacted: true|false }
```

### フロントエンド: ReactionButton コンポーネント

- 👍ボタン + カウント表示
- `session_id` は `localStorage` に保存（UUID v4）
- トグル動作（押したら取り消し可能）

### 好み分析サービス: `worker/preference_analyzer.py`

```python
class PreferenceAnalyzer:
    async def analyze_channel(self, channel_id) -> ChannelPreference:
        # 直近N曲のreaction率を計算
        # 高評価トラックのキャプション共通要素を抽出
        # → ChannelPreference(preferred_keywords, preferred_bpm_range, preferred_key)

    def enhance_prompt(self, base_prompt: str, preference: ChannelPreference) -> str:
        # 「リスナーに人気の要素: {keywords}」をプロンプトに注入
```

---

## F4: チャンネル設定と自動生成

### channels テーブル拡張

```sql
ALTER TABLE channels ADD COLUMN mood_description TEXT;          -- 雰囲気の説明
ALTER TABLE channels ADD COLUMN auto_generate BOOLEAN DEFAULT true;
ALTER TABLE channels ADD COLUMN min_stock INTEGER DEFAULT 5;    -- 最小ストック数
ALTER TABLE channels ADD COLUMN max_stock INTEGER DEFAULT 50;   -- 最大ストック数
```

### APIエンドポイント

```
PATCH /api/channels/{slug}
  Body: { mood_description?, auto_generate?, min_stock?, max_stock? }
  → 200 { ok: true }
```

### 自動生成ジョブ: `worker/auto_generator.py`

```python
class AutoGenerator:
    """チャンネルのストックが min_stock を下回ったら自動生成"""

    async def check_and_generate(self):
        for channel in active_channels:
            if not channel.auto_generate:
                continue
            stock = await count_tracks(channel.id)
            if stock < channel.min_stock:
                if not self._check_system_resources():
                    continue  # リソース不足時はスキップ
                await create_auto_request(channel)

    def _check_system_resources(self) -> bool:
        cpu = psutil.cpu_percent(interval=1)
        mem = psutil.virtual_memory().percent
        return cpu < 80 and mem < 85
```

- 自動生成は `mood_description` を使って Claude API で歌詞生成
- Worker のポーリングループに統合（60秒間隔でストック確認）

---

## F5: ラジオ再生改善

### 楽曲棚卸しロジック

```python
async def retire_tracks(channel_id):
    """再生回数に対する👍比率が低い曲を退役"""
    tracks = await get_tracks_with_stats(channel_id)
    for track in tracks:
        if track.play_count >= 5:  # 最低5回再生後に判定
            like_ratio = track.like_count / track.play_count
            if like_ratio < 0.1:  # 10%未満は退役候補
                await mark_retired(track.id)
```

### tracks テーブル拡張

```sql
ALTER TABLE tracks ADD COLUMN is_retired BOOLEAN DEFAULT false;
ALTER TABLE tracks ADD COLUMN like_count INTEGER DEFAULT 0;  -- 非正規化キャッシュ
```

### 重み付きシャッフル

Liquidsoap の `playlist` は単純ランダムなので、API側でプレイリストファイルを動的生成:

```python
async def generate_weighted_playlist(channel_id) -> str:
    """👍数に基づく重み付きプレイリストを m3u 形式で生成"""
    tracks = await get_active_tracks(channel_id)
    lines = []
    for t in tracks:
        weight = max(1, t.like_count)  # 最低1回は出現
        for _ in range(weight):
            lines.append(f"/tracks/{t.file_path}")
    random.shuffle(lines)
    return "\n".join(lines)
```

- `generated_tracks/{channel}/playlist.m3u` を定期更新（5分間隔）
- Liquidsoap を playlist ファイル参照に変更

### channel.liq 変更

```liquidsoap
# 重み付きプレイリストファイルを使用
tracks = playlist(
  mode="normal",       # ファイル順に再生（事前にシャッフル済み）
  reload_mode="watch",
  "/tracks/{CHANNEL}/playlist.m3u"
)
```

---

## F6: ANTHROPIC_API_KEY 管理

- `.env.example` に `ANTHROPIC_API_KEY=` を追加
- Worker の `config.py` に `anthropic_api_key` フィールド追加
- API側では `ANTHROPIC_API_KEY` 環境変数から読み取り
- フロントエンドには一切送信しない
- Claude API 呼び出しはサーバーサイド（API or Worker）のみ

---

## Phase 2 設計メモ（将来実装）

### プレイリスト（マイアルバム）

```sql
CREATE TABLE playlists (
  id UUID PRIMARY KEY,
  session_id VARCHAR(100) NOT NULL,
  name TEXT NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE playlist_tracks (
  playlist_id UUID REFERENCES playlists(id),
  track_id UUID REFERENCES tracks(id),
  position INTEGER NOT NULL,
  added_at TIMESTAMPTZ DEFAULT NOW(),
  PRIMARY KEY (playlist_id, track_id)
);
```

- プレイリスト内の楽曲傾向を分析し、ユーザー好みプロファイルとして生成に反映
- 個別再生モード: HLS or on-demand FLAC配信（Icecastとは別経路）

---

## DBマイグレーション計画

### Migration 003: Phase 1 スキーマ拡張

```sql
-- requests テーブル拡張
ALTER TABLE requests ADD COLUMN mood TEXT;

-- tracks テーブル拡張
ALTER TABLE tracks ADD COLUMN title TEXT;
ALTER TABLE tracks ADD COLUMN mood TEXT;
ALTER TABLE tracks ADD COLUMN is_retired BOOLEAN DEFAULT false;
ALTER TABLE tracks ADD COLUMN like_count INTEGER DEFAULT 0;

-- channels テーブル拡張
ALTER TABLE channels ADD COLUMN mood_description TEXT;
ALTER TABLE channels ADD COLUMN auto_generate BOOLEAN DEFAULT true;
ALTER TABLE channels ADD COLUMN min_stock INTEGER DEFAULT 5;
ALTER TABLE channels ADD COLUMN max_stock INTEGER DEFAULT 50;

-- reactions テーブル新規
CREATE TABLE reactions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  track_id UUID NOT NULL REFERENCES tracks(id),
  session_id VARCHAR(100) NOT NULL,
  reaction_type VARCHAR(20) NOT NULL DEFAULT 'like',
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE (track_id, session_id)
);
CREATE INDEX idx_reactions_track ON reactions(track_id);
```

---

## 実装順序

| PR | Issue | 内容 | 依存 |
|----|-------|------|------|
| 1 | #22 | DBスキーマ拡張（Migration 003） | なし |
| 2 | #23 | 歌詞・曲名自動生成（Claude API統合） | #22 |
| 3 | #24 | 楽曲情報表示（曲名・歌詞表示UI） | #22 |
| 4 | #25 | フィードバックシステム（API + UI） | #22 |
| 5 | #26 | チャンネル自動生成ジョブ | #22, #23 |
| 6 | #27 | ラジオ再生改善（棚卸し + 重み付きシャッフル） | #22, #25 |
| 7 | #28 | 結合テスト + ドキュメント更新 | #22-#27 |

---

## テスト方針

- 各PRで単体テスト必須
- Claude API呼び出しはモック（httpx mock）
- DB操作は実際のPostgreSQL（テスト用DB）
- フロントエンドはVitest + React Testing Library
- 結合テスト: docker compose up → API経由で mood リクエスト → トラック生成確認
