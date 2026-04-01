# SDD #904 — リクエスト投票 + 人気楽曲ランキング

## メタデータ
| 項目 | 内容 |
|------|------|
| Issue | #904 |
| 機能名 | リクエスト投票 + 人気楽曲ランキング |
| ステータス | 実装中 |
| 作成日 | 2026-04-01 |
| 担当 Director | AI Director |

---

## 1. 背景・目的

AI Music Station ではユーザーが楽曲生成をリクエストできるが、複数のリクエストが溜まった場合にどれを優先して生成するかの仕組みがなかった。
本機能はリスナーが「聴きたいリクエストに投票する」ことで優先度を表明でき、かつ「人気の楽曲（いいね数ベース）のランキング」を可視化することで、コミュニティ参加感を高める。

---

## 2. 既存実装との関係

| 機能 | 既存 | 今回追加 |
|------|------|--------|
| トラックへのいいね（Reaction） | ✅ reactions テーブル / ReactionButton.tsx | — |
| リクエスト登録 | ✅ requests テーブル / RequestQueueTab.tsx | — |
| **リクエストへの投票** | ❌ | ✅ request_votes テーブル + API + UI |
| **人気楽曲ランキング** | ❌ | ✅ GET /api/channels/{slug}/ranking + ChannelRanking.tsx |

---

## 3. 機能要件 (FR)

### FR-1: リクエスト投票
- ユーザー（session_id ベース）は pending 状態のリクエストに1票を投じることができる
- 同一 session_id・同一 request_id の重複投票は不可（一意制約）
- 投票を取り消すことができる
- 投票数は `requests.vote_count` に非正規化してアトミック更新する

### FR-2: 投票順ソート
- RequestQueueTab にて pending リクエストを `vote_count DESC, created_at ASC` でソートして表示する
- 投票数がゼロのリクエストも表示する

### FR-3: 人気楽曲ランキング
- チャンネル別 Top 5 トラックを `like_count DESC` で取得できる API エンドポイントを追加
- is_retired=false のトラックのみ対象
- 最低 `like_count > 0` のトラックを優先表示（全てゼロでも表示は行う）

### FR-4: ランキング UI
- QUEUE タブ内にランキングコンポーネントを追加
- チャンネル別切り替えまたは全チャンネル横断表示
- 現在選択中のチャンネルのランキングを表示

---

## 4. 受け入れ条件 (AC)

| ID | 条件 |
|----|------|
| AC-1 | 同一 session_id が同一 request_id に2回投票すると 409 を返す |
| AC-2 | 投票後に `requests.vote_count` が +1 される（アトミック） |
| AC-3 | 投票取消後に `requests.vote_count` が -1 される（0未満にならない） |
| AC-4 | GET `/api/channels/{slug}/ranking` が最大 5 件の `like_count DESC` トラックを返す |
| AC-5 | ChannelRanking.tsx が QUEUE タブ内に表示され、1〜5位の楽曲を表示する |
| AC-6 | RequestQueueTab が vote_count DESC でソートされて表示される |
| AC-7 | RequestVoteButton が投票済みの場合に視覚的に区別された状態を表示する |

---

## 5. DB スキーマ

### 新テーブル: `request_votes`
```sql
CREATE TABLE request_votes (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  request_id  UUID NOT NULL REFERENCES requests(id),
  session_id  VARCHAR(100) NOT NULL,
  created_at  TIMESTAMPTZ DEFAULT now()
);
CREATE UNIQUE INDEX uq_request_votes_request_session
  ON request_votes(request_id, session_id);
CREATE INDEX idx_request_votes_request
  ON request_votes(request_id);
```

### 変更: `requests` テーブル
```sql
ALTER TABLE requests ADD COLUMN vote_count INTEGER NOT NULL DEFAULT 0;
```

---

## 6. API 設計

### 6.1 リクエスト投票 POST
```
POST /api/requests/{request_id}/votes
Body: { "session_id": string }
Response: { "ok": true, "count": int }
Errors: 404 (request not found), 409 (already voted)
```

### 6.2 リクエスト投票取消 DELETE
```
DELETE /api/requests/{request_id}/votes
Body: { "session_id": string }
Response: { "ok": true, "count": int }
Errors: 404 (vote not found)
```

### 6.3 投票状態取得 GET
```
GET /api/requests/{request_id}/votes?session_id={session_id}
Response: { "count": int, "user_voted": bool }
```

### 6.4 人気楽曲ランキング GET
```
GET /api/channels/{slug}/ranking?limit=5
Response: {
  "tracks": [
    { "rank": int, "id": UUID, "title": string|null, "caption": string,
      "like_count": int, "play_count": int, "duration_ms": int|null,
      "bpm": int|null }
  ],
  "channel_slug": str
}
```

---

## 7. フロントエンド設計

### 7.1 新コンポーネント

#### `RequestVoteButton.tsx`
- Props: `requestId: string`
- 内部で sessionId 管理（ReactionButton.tsx と同パターン）
- 投票済み: 塗りつぶしボタン、未投票: アウトラインボタン
- pending 状態のリクエストのみ表示（completed/failed は非表示）

#### `ChannelRanking.tsx`
- Props: `channelSlug: string`
- GET `/api/channels/{slug}/ranking` をポーリング（30秒間隔）
- Top 5 を 1〜5 の番号付きリストで表示
- like_count が 0 の場合はランキング非表示（「まだランキングデータがありません」）

### 7.2 既存コンポーネント変更

#### `RequestQueueTab.tsx`
- vote_count を RequestDetailResponse に追加
- pending リクエストの表示順を vote_count DESC に変更
- 各リクエスト行に `RequestVoteButton` を追加

---

## 8. ロールバック方針

1. マイグレーション: `alembic downgrade 011` で `request_votes` テーブル・`vote_count` カラムを削除
2. フロントエンド: feature branch を revert、re-deploy
3. データ損失: `request_votes` データのみ消失（他データへの影響なし）

---

## 9. 非機能要件

- ランキング API のレスポンスタイム: 200ms 以内（インデックスあり）
- `vote_count` アトミック更新: `UPDATE ... SET vote_count = vote_count + 1 WHERE id = ?`

---

## 10. テスト方針

- Unit: 投票 API の 409 重複エラー、vote_count アトミック更新
- Integration: 投票→取消のライフサイクル、ランキング順序
- E2E: RequestVoteButton クリック → vote_count 反映確認
