# API設計書 — プレイリスト機能

## 概要

AI Music Station のプレイリスト機能 REST API。
既存の FastAPI + SQLAlchemy AsyncSession パターンに準拠した設計。

---

## 共通仕様

| 項目         | 値                                   |
|------------|--------------------------------------|
| ベースURL    | `/api/playlists`                     |
| 認証         | なし（現時点で認証機構なし）             |
| コンテンツタイプ | `application/json`               |
| 文字コード     | UTF-8                               |
| タイムゾーン   | UTC（ISO 8601形式: `2026-03-27T12:00:00Z`）|

### エラーレスポンス共通形式

```json
{
  "detail": "エラーメッセージ（日本語）"
}
```

| HTTPステータス | 発生条件                                              |
|-------------|-----------------------------------------------------|
| 400         | リクエストボディのバリデーションエラー                    |
| 404         | 指定IDのプレイリストまたはトラックが存在しない             |
| 409         | 重複追加（同一トラックがすでにプレイリスト内に存在）         |
| 422         | Pydantic バリデーションエラー（FastAPI自動）              |

---

## エンドポイント一覧

| メソッド | パス                                         | 説明                       |
|--------|---------------------------------------------|----------------------------|
| GET    | `/api/playlists`                            | プレイリスト一覧取得           |
| POST   | `/api/playlists`                            | プレイリスト作成               |
| GET    | `/api/playlists/{playlist_id}`              | プレイリスト詳細取得（トラック含む） |
| PUT    | `/api/playlists/{playlist_id}`              | プレイリストメタデータ更新         |
| DELETE | `/api/playlists/{playlist_id}`              | プレイリスト削除               |
| POST   | `/api/playlists/{playlist_id}/tracks`       | トラック追加                   |
| DELETE | `/api/playlists/{playlist_id}/tracks/{track_id}` | トラック削除              |
| PUT    | `/api/playlists/{playlist_id}/tracks/reorder` | トラック並べ替え              |

---

## 各エンドポイント詳細

---

### GET /api/playlists — プレイリスト一覧取得

**クエリパラメータ:**

| パラメータ  | 型       | 必須 | デフォルト | 説明                                         |
|-----------|---------|------|-----------|----------------------------------------------|
| user_id   | string  | No   | なし      | 指定時: 該当ユーザーのプレイリストのみ返す        |
| public    | boolean | No   | なし      | `true`: 公開のみ, `false`: 非公開のみ, 省略: 全件  |
| limit     | integer | No   | 20        | 取得件数上限（1〜100）                          |
| offset    | integer | No   | 0         | ページングオフセット                             |

**レスポンス: 200 OK**

```json
{
  "playlists": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "name": "朝の作業BGM",
      "description": "集中できる穏やかな曲集",
      "user_id": "session-abc123",
      "is_public": true,
      "track_count": 5,
      "created_at": "2026-03-27T09:00:00Z",
      "updated_at": "2026-03-27T10:30:00Z"
    }
  ],
  "total": 1
}
```

---

### POST /api/playlists — プレイリスト作成

**リクエストボディ:**

```json
{
  "name": "朝の作業BGM",
  "description": "集中できる穏やかな曲集",
  "user_id": "session-abc123",
  "is_public": true
}
```

| フィールド    | 型       | 必須 | バリデーション          | 説明                    |
|------------|---------|------|----------------------|-------------------------|
| name       | string  | Yes  | 1〜100文字             | プレイリスト名            |
| description | string | No   | 最大1000文字           | 説明文                   |
| user_id    | string  | No   | 最大100文字, \w-_のみ   | 作成者識別子              |
| is_public  | boolean | No   | —                    | 公開フラグ（デフォルト: true） |

**レスポンス: 201 Created**

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "朝の作業BGM",
  "description": "集中できる穏やかな曲集",
  "user_id": "session-abc123",
  "is_public": true,
  "track_count": 0,
  "created_at": "2026-03-27T09:00:00Z",
  "updated_at": "2026-03-27T09:00:00Z"
}
```

---

### GET /api/playlists/{playlist_id} — プレイリスト詳細取得

**パスパラメータ:**

| パラメータ      | 型     | 説明              |
|---------------|-------|------------------|
| playlist_id   | UUID  | プレイリストID      |

**レスポンス: 200 OK**

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "朝の作業BGM",
  "description": "集中できる穏やかな曲集",
  "user_id": "session-abc123",
  "is_public": true,
  "track_count": 2,
  "created_at": "2026-03-27T09:00:00Z",
  "updated_at": "2026-03-27T10:30:00Z",
  "tracks": [
    {
      "playlist_track_id": "660e8400-e29b-41d4-a716-446655440001",
      "position": 0,
      "added_at": "2026-03-27T09:05:00Z",
      "track": {
        "id": "770e8400-e29b-41d4-a716-446655440002",
        "title": "Morning Flow",
        "caption": "穏やかな朝のピアノ曲",
        "mood": "calm",
        "duration_ms": 180000,
        "bpm": 90,
        "music_key": "C",
        "instrumental": true,
        "play_count": 42,
        "like_count": 7,
        "created_at": "2026-03-26T08:00:00Z"
      }
    }
  ]
}
```

**エラー:**
- `404 Not Found` — プレイリストが存在しない

---

### PUT /api/playlists/{playlist_id} — プレイリスト更新

**パスパラメータ:**

| パラメータ      | 型     | 説明              |
|---------------|-------|------------------|
| playlist_id   | UUID  | プレイリストID      |

**リクエストボディ:**

```json
{
  "name": "夜の作業BGM",
  "description": "落ち着いた夜の曲集",
  "is_public": false
}
```

| フィールド    | 型       | 必須 | バリデーション     | 説明                |
|------------|---------|------|-----------------|---------------------|
| name       | string  | Yes  | 1〜100文字        | プレイリスト名        |
| description | string | No   | 最大1000文字      | 説明文               |
| is_public  | boolean | Yes  | —               | 公開フラグ            |

**レスポンス: 200 OK** — 更新後のプレイリスト（詳細形式と同じ構造、tracks含む）

**エラー:**
- `404 Not Found` — プレイリストが存在しない

---

### DELETE /api/playlists/{playlist_id} — プレイリスト削除

**パスパラメータ:**

| パラメータ      | 型     | 説明              |
|---------------|-------|------------------|
| playlist_id   | UUID  | プレイリストID      |

**レスポンス: 200 OK**

```json
{
  "ok": true,
  "deleted_tracks": 5
}
```

**エラー:**
- `404 Not Found` — プレイリストが存在しない

**注:** プレイリスト削除時、関連する `playlist_tracks` レコードはDBのCASCADE DELETEにより自動削除される。`tracks` テーブル自体は削除しない。

---

### POST /api/playlists/{playlist_id}/tracks — トラック追加

**パスパラメータ:**

| パラメータ      | 型     | 説明              |
|---------------|-------|------------------|
| playlist_id   | UUID  | プレイリストID      |

**リクエストボディ:**

```json
{
  "track_id": "770e8400-e29b-41d4-a716-446655440002"
}
```

| フィールド  | 型    | 必須 | 説明             |
|-----------|------|------|-----------------|
| track_id  | UUID | Yes  | 追加するトラックID |

**処理詳細:**
- position は既存トラックの最大 position + 1 を自動設定（末尾追加）
- 既存トラックが0件の場合は position=0

**レスポンス: 201 Created**

```json
{
  "playlist_track_id": "880e8400-e29b-41d4-a716-446655440003",
  "playlist_id": "550e8400-e29b-41d4-a716-446655440000",
  "track_id": "770e8400-e29b-41d4-a716-446655440002",
  "position": 2,
  "added_at": "2026-03-27T11:00:00Z"
}
```

**エラー:**
- `404 Not Found` — プレイリストまたはトラックが存在しない（または `is_retired=true`）
- `409 Conflict` — 同一トラックが既にプレイリストに含まれている

---

### DELETE /api/playlists/{playlist_id}/tracks/{track_id} — トラック削除

**パスパラメータ:**

| パラメータ      | 型     | 説明              |
|---------------|-------|------------------|
| playlist_id   | UUID  | プレイリストID      |
| track_id      | UUID  | トラックID         |

**処理詳細:**
- 指定トラックを削除後、残りトラックの position を詰める（position の連続性を維持）
- 例: positions [0, 1, 2] から position=1 を削除 → [0, 1] に更新

**レスポンス: 200 OK**

```json
{
  "ok": true
}
```

**エラー:**
- `404 Not Found` — プレイリストが存在しない、またはトラックがプレイリストに含まれていない

---

### PUT /api/playlists/{playlist_id}/tracks/reorder — トラック並べ替え

**パスパラメータ:**

| パラメータ      | 型     | 説明              |
|---------------|-------|------------------|
| playlist_id   | UUID  | プレイリストID      |

**リクエストボディ:**

```json
{
  "track_ids": [
    "770e8400-e29b-41d4-a716-446655440002",
    "880e8400-e29b-41d4-a716-446655440003",
    "990e8400-e29b-41d4-a716-446655440004"
  ]
}
```

| フィールド   | 型          | 必須 | バリデーション                            | 説明                                                    |
|-----------|------------|------|----------------------------------------|---------------------------------------------------------|
| track_ids | UUID[]     | Yes  | 1〜1000件, プレイリスト内の全トラックIDを含む | 新しい順序でのトラックID配列。配列の添え字が新しいpositionになる |

**処理詳細:**
1. `track_ids` が現在のプレイリスト内トラックIDセットと一致することを検証（欠けや余分があれば400）
2. トランザクション内で全 `playlist_tracks` の position を一括更新
3. `playlists.updated_at` を更新

**レスポンス: 200 OK** — 更新後のプレイリスト詳細（tracks 含む）

**エラー:**
- `400 Bad Request` — `track_ids` がプレイリスト内トラックセットと不一致
- `404 Not Found` — プレイリストが存在しない

---

## Pydantic スキーマ定義（参考実装）

`api/schemas.py` への追記内容:

```python
# --- Playlist ---

class PlaylistTrackItem(BaseModel):
    playlist_track_id: uuid.UUID
    position: int
    added_at: datetime
    track: TrackResponse


class PlaylistResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None = None
    user_id: str | None = None
    is_public: bool
    track_count: int
    created_at: datetime
    updated_at: datetime


class PlaylistDetailResponse(PlaylistResponse):
    tracks: list[PlaylistTrackItem]


class PlaylistListResponse(BaseModel):
    playlists: list[PlaylistResponse]
    total: int


class PlaylistCreateBody(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: str | None = Field(None, max_length=1000)
    user_id: str | None = Field(
        None,
        max_length=100,
        pattern=r'^[a-zA-Z0-9_\-]+$',
    )
    is_public: bool = True


class PlaylistUpdateBody(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: str | None = Field(None, max_length=1000)
    is_public: bool


class PlaylistAddTrackBody(BaseModel):
    track_id: uuid.UUID


class PlaylistAddTrackResponse(BaseModel):
    playlist_track_id: uuid.UUID
    playlist_id: uuid.UUID
    track_id: uuid.UUID
    position: int
    added_at: datetime


class PlaylistReorderBody(BaseModel):
    track_ids: list[uuid.UUID] = Field(..., min_length=1, max_length=1000)


class PlaylistDeleteResponse(BaseModel):
    ok: bool
    deleted_tracks: int
```

---

## ルーター構成

- ファイル: `api/routers/playlists.py`
- `api/main.py` の `include_router` に追加: `from api.routers import playlists` → `app.include_router(playlists.router)`

---

## セキュリティ設計

### 入力値バリデーション・サニタイズ方針

| 入力項目       | バリデーション方針                                                  |
|-------------|------------------------------------------------------------------|
| name        | Pydantic `min_length=1, max_length=100`。HTML/SQLの特殊文字はそのまま保存（表示時のエスケープはフロントエンド責務）|
| description | Pydantic `max_length=1000`。同上                                  |
| user_id     | `pattern=r'^[a-zA-Z0-9_\-]+'` によりパス・クエリインジェクション文字を排除 |
| track_id    | Pydantic `uuid.UUID` 型によりUUID形式以外は422で自動拒否              |
| playlist_id | パスパラメータ。FastAPI の UUID 型変換で形式バリデーション               |
| position    | DB CHECK制約 `position >= 0` で負数を排除                           |
| track_ids（reorder） | `max_length=1000` で大量データ攻撃を制限。アプリレイヤーでセット一致検証 |

### SQLインジェクション対策
- 全クエリは SQLAlchemy ORM / Core を使用。生SQL文字列連結は行わない

### その他
- user_id はサーバーサイドで発行・検証しない（現在の仕様）。将来的な認証追加時に制約を追加する
- プレイリストへのアクセス制御は is_public フラグのみで管理（今回スコープ）

---

## 非機能要件

### パフォーマンス目標

| 操作                              | 目標レスポンスタイム |
|----------------------------------|------------------|
| 一覧取得（20件）                    | < 100ms           |
| 詳細取得（トラック100件）             | < 200ms           |
| トラック追加/削除                    | < 100ms           |
| 並べ替え（100件）                   | < 200ms           |

### スケーラビリティ
- 1プレイリストあたりのトラック数上限: 1000件（`track_ids` バリデーションで制限）
- ユーザーあたりのプレイリスト数: 制限なし（現時点。乱用はレート制限で別途対処）

### テスタビリティ（AC記述指針）
- 各エンドポイントに対して「正常系・異常系・境界値」のテストケースを定義可能な設計
- 副作用（DB更新）は単一操作にまとめ、テストのセットアップ/クリーンアップを容易に
- 並行性テストケース候補:
  - 同一プレイリストへの同時トラック追加（UNIQUE制約によるIntegrityError処理）
  - 同時並べ替えリクエスト（Last-Write-Wins が正しく機能すること）
