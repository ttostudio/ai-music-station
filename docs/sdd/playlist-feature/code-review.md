---
reviewer-role: Code Reviewer
gate: Gate-4
status: conditional-pass
date: 2026-03-27
---

# コードレビュー — プレイリスト機能

**レビュー日**: 2026-03-27
**レビュアー**: Code Reviewer（独立エージェント）

> ⚠️ 前回のレビューは CEO 代行によるものであり独立性要件を満たしていなかった。本レビューが正式版。

---

## 総合判定: **Conditional Pass**

セキュリティ・アーキテクチャは良好。Critical 1 件・Major 3 件の修正が必須。
修正完了後は再レビューなしで Gate 5（テスト実行）へ進んでよい。

---

## 指摘事項一覧

### Critical

#### CR-001: `addTrackToPlaylist` のリクエストボディが BE 仕様と不一致

- **ファイル**: `frontend/src/api/playlists.ts:89`
- **内容**: フロントエンドが `{ track_id: trackId }` を送信しているが、バックエンドの `AddTrackBody` は `{ track_ids: ["uuid", ...] }` (配列) を期待している。このままでは **422 Validation Error** が常に返り、**トラック追加機能が完全に動作しない**。

```diff
- body: JSON.stringify({ track_id: trackId }),
+ body: JSON.stringify({ track_ids: [trackId] }),
```

さらに `types.ts` の `PlaylistAddTrackResponse` 型（`playlist_id, track_id, position, added_at`）も実際の `AddTracksResponse`（`playlist_id, added: [{track_id, position, added_at}]`）と乖離している。`addTrackToPlaylist` の返り値型も合わせて修正すること。

---

### Major

#### CR-002: DELETE エンドポイントが 204 を返すが、フロントエンドが JSON パースを試みる

- **ファイル**:
  - `frontend/src/api/playlists.ts:71-78` (`deletePlaylist`)
  - `frontend/src/api/playlists.ts:93-101` (`removeTrackFromPlaylist`)
- **内容**: バックエンドは DELETE 系エンドポイントを `204 No Content`（ボディなし）で返す。`fetchJSON` は常に `response.json()` を呼ぶため、空ボディに対して `SyntaxError` が発生し**プレイリスト削除・トラック削除が機能しない**。
- **修正案**: `fetchJSON` に 204 のショートサーキットを追加する。

```ts
if (response.status === 204) return undefined as T;
return response.json() as Promise<T>;
```

または `deletePlaylist` / `removeTrackFromPlaylist` のみ `fetch` 直呼びにしてボディ解析を省略する。

#### CR-003: `list_playlists` の N+1 クエリ

- **ファイル**: `api/routers/playlists.py:141-153`
- **内容**: プレイリスト一覧取得時に `_track_count` を各プレイリストに対してループ内で個別実行している。50 件なら 51 クエリが発行され、NFR-002（P95 < 200ms）の達成が困難。
- **修正**: `playlist_tracks` を `GROUP BY` でまとめてカウントするサブクエリを使う。

```python
count_sub = (
    select(PlaylistTrack.playlist_id, func.count().label("cnt"))
    .group_by(PlaylistTrack.playlist_id)
    .subquery()
)
rows = await db.execute(
    select(Playlist, func.coalesce(count_sub.c.cnt, 0).label("track_count"))
    .outerjoin(count_sub, Playlist.id == count_sub.c.playlist_id)
    .where(Playlist.session_id == session_id)
    .order_by(Playlist.created_at.desc())
    .limit(limit).offset(offset)
)
```

#### CR-004: `likes` タブが FR-008 未実装（`TrackHistory` を流用している）

- **ファイル**: `frontend/src/components/layouts/MobileLayout.tsx:205-217`
- **内容**: `activeTab === "likes"` のとき `TrackHistory`（再生履歴）をそのまま表示しており、`GET /api/favorites` を使ったお気に入りトラック一覧ではない。FR-008「お気に入りトラックを一覧表示できる」が未達成。
- **修正**: `getFavorites` を呼ぶコンポーネントを実装して差し替える。

---

### Minor

#### CR-005: `PlaylistCreateModal` の文字数上限が SDD 仕様より厳しい

- **ファイル**: `frontend/src/components/PlaylistCreateModal.tsx:13-14`
- **内容**: `NAME_MAX=50`・`DESC_MAX=200` と定義されているが、SDD（api-spec.md）は名前 100 文字・説明 500 文字。バックエンドは受け付けるが UI 側で弾いている。
- **修正**: `NAME_MAX=100`、`DESC_MAX=500` に合わせる。

#### CR-006: `fetchAllTracks` が毎レンダーで新参照を生成（不要な再フェッチの可能性）

- **ファイル**: `frontend/src/components/layouts/MobileLayout.tsx:50-55`
- **内容**: `fetchAllTracks` はコンポーネント関数内にインライン定義されており、`MobileLayout` がレンダーされるたびに新しい関数参照が生まれる。`TrackSelectModal` の `useEffect` がこれを依存に持つと不要な API 再フェッチが起きうる。
- **修正**: `useCallback` でメモ化する（`channels` を依存配列に）。

#### CR-007: `createPlaylist` の返り値型が実際のレスポンスと異なる

- **ファイル**: `frontend/src/api/playlists.ts:54`
- **内容**: `PlaylistDetail`（`tracks` フィールドあり）を返すと宣言されているが、`POST /api/playlists` レスポンスには `tracks` がない。呼び出し元が `tracks` にアクセスすると実行時エラーになりうる。
- **修正**: 返り値型を `Promise<Playlist>` に変更する。

---

## ファイル別評価

| ファイル | 評価 | 主要理由 |
|--------|------|---------|
| `alembic/versions/009_add_playlists.py` | ✅ Pass | CASCADE・インデックス・UNIQUE 制約すべて正しい。downgrade も完全 |
| `api/routers/playlists.py` | ⚠️ Conditional | N+1 クエリ (CR-003) 以外は良好 |
| `api/schemas.py` | ✅ Pass | Pydantic バリデーションが SDD に準拠 |
| `api/main.py` | ✅ Pass | ルーター登録のみ、問題なし |
| `worker/models.py` | ✅ Pass | `onupdate=func.now()`・リレーション・インデックス適切 |
| `frontend/src/api/playlists.ts` | ❌ Critical | CR-001・CR-002 要修正 |
| `frontend/src/api/types.ts` | ⚠️ Conditional | CR-001・CR-007 の型修正が必要 |
| `frontend/src/components/PlaylistList.tsx` | ✅ Pass | エラー・ローディング・空状態すべて対応 |
| `frontend/src/components/PlaylistDetail.tsx` | ✅ Pass | 楽観的 UI 更新・ドラッグ&ドロップ実装良好 |
| `frontend/src/components/PlaylistCard.tsx` | ✅ Pass | aria 属性・キーボード対応あり |
| `frontend/src/components/PlaylistTrackItem.tsx` | ✅ Pass | `useSortable` 実装正確 |
| `frontend/src/components/PlaylistCreateModal.tsx` | ⚠️ Minor | CR-005（文字数上限）のみ |
| `frontend/src/components/TrackSelectModal.tsx` | ✅ Pass | `cancelled` フラグによるクリーンアップ良好 |
| `frontend/src/App.tsx` | ✅ Pass | プレイリスト状態管理の統合は正しい |
| `frontend/src/components/TabBar.tsx` | ✅ Pass | ARIA タブパターン準拠 |
| `frontend/src/components/layouts/MobileLayout.tsx` | ⚠️ Major | CR-004（likes タブ未実装）・CR-006 |

---

## セキュリティチェック結果

| チェック項目 | 結果 | 備考 |
|------------|------|------|
| CR-S01: XSS | ✅ 問題なし | JSX エスケープにより安全。`dangerouslySetInnerHTML` 不使用 |
| CR-S02: DOM 直接操作 | ✅ 問題なし | 直接 DOM 操作なし |
| SQL インジェクション | ✅ 問題なし | SQLAlchemy ORM + パラメータバインド使用 |
| 認可チェック | ✅ 問題なし | 全変更エンドポイントで `_check_owner` による session_id 検証あり |
| session_id 漏洩 | ✅ 問題なし | `PlaylistResponse` 等のレスポンスに session_id は含まれない |

---

## プロセスチェック結果

| チェック項目 | 結果 |
|------------|------|
| CR-P01: CHANGELOG.md | PR マージ時追記予定であれば問題なし |
| CR-P02: デバッグコード残存 | ✅ なし（`console.log` / `print` 確認済み） |

---

## 修正優先度サマリー

| 優先度 | 件数 | Gate 5 前に必須 |
|--------|------|----------------|
| Critical | 1 | ✅ はい |
| Major | 3 | ✅ はい |
| Minor | 3 | 推奨（Gate 5 後でも可） |

**Critical / Major の修正確認後、再レビューなしで Gate 5 に進んでよい。**
