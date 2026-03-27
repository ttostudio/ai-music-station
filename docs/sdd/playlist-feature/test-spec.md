---
issue: "#28"
version: "1.0"
author-role: Director
gate: Gate-1
status: draft
---

# テスト仕様書 — プレイリスト機能

## テスト戦略

V字モデルに準拠し、単体テスト・結合テスト・E2Eテストを実施する。

```
要件定義 ←────────────────────────→ E2E テスト（AC検証）
  API仕様 ←──────────────────────→ 結合テスト（API テスト）
    実装 ←────────────────────────→ 単体テスト（ユニットテスト）
```

---

## テスト環境

| 環境 | 説明 |
|------|------|
| 単体テスト | pytest + pytest-asyncio（バックエンド）、Vitest（フロントエンド） |
| 結合テスト | pytest + httpx（FastAPI TestClient）+ PostgreSQL（docker-compose test profile） |
| E2E テスト | Playwright + 実稼働 Docker Compose |

---

## テストケース一覧

### 1. 単体テスト — API バリデーション

| TC-ID | 対象 | テストケース | 期待結果 |
|-------|------|------------|---------|
| UT-001 | POST /api/playlists | name が空文字の場合 | 400 Bad Request |
| UT-002 | POST /api/playlists | name が101文字の場合 | 400 Bad Request |
| UT-003 | POST /api/playlists | description が501文字の場合 | 400 Bad Request |
| UT-004 | POST /api/playlists | X-Session-ID ヘッダーなしの場合 | 400 Bad Request |
| UT-005 | PATCH /api/playlists/{id} | name を空文字に更新しようとした場合 | 400 Bad Request |
| UT-006 | PUT reorder | track_ids に存在しない UUID が含まれる | 400 Bad Request |
| UT-007 | PUT reorder | track_ids の件数がプレイリストのトラック数と異なる | 400 Bad Request |

### 2. 単体テスト — ビジネスロジック

| TC-ID | 対象 | テストケース | 期待結果 |
|-------|------|------------|---------|
| UT-101 | session_id チェック | 他セッションのプレイリスト取得 | 403 Forbidden |
| UT-102 | session_id チェック | 他セッションのプレイリスト削除 | 403 Forbidden |
| UT-103 | session_id チェック | 他セッションへのトラック追加 | 403 Forbidden |
| UT-104 | 重複チェック | 同一トラックを2回追加 | 409 Conflict |
| UT-105 | 重複チェック | 同一セッションで同名プレイリスト作成 | 409 Conflict |
| UT-106 | 上限チェック | 200件を超えるトラックを追加 | 422 Unprocessable Entity |
| UT-107 | 論理削除 | is_deleted=true のプレイリストを GET | 404 Not Found |
| UT-108 | retired トラック | is_retired=true のトラックを追加 | 404 Not Found |

### 3. 結合テスト — CRUD フロー

| TC-ID | シナリオ | 手順 | 期待結果 |
|-------|--------|------|---------|
| IT-001 | プレイリスト作成 | POST /api/playlists → DB確認 | レコード1件挿入、レスポンスに UUID |
| IT-002 | プレイリスト一覧 | 3件作成後 GET /api/playlists | 3件返却、created_at 降順 |
| IT-003 | プレイリスト詳細 | トラック追加後 GET /api/playlists/{id} | tracks 配列に position 昇順でトラック含む |
| IT-004 | プレイリスト更新 | PATCH で name 変更 → GET 確認 | updated_at が更新され name が変更されている |
| IT-005 | プレイリスト削除 | DELETE → GET | 404 Not Found |
| IT-006 | CASCADE 削除 | 削除後 playlist_tracks テーブル確認 | 関連レコードが全て削除されている |
| IT-007 | トラック追加 | POST /api/playlists/{id}/tracks | position が末尾(N)に追加される |
| IT-008 | トラック削除 | トラック削除後 GET 詳細 | position が詰められて返る |
| IT-009 | 並べ替え | 3件追加後 PUT reorder で逆順 | GET 詳細で逆順の position で返る |
| IT-010 | お気に入り一覧 | 3件リアクション後 GET /api/favorites | 3件返却、liked_at 降順 |

### 4. 結合テスト — エラーハンドリング

| TC-ID | シナリオ | 期待結果 |
|-------|--------|---------|
| IT-101 | 存在しない playlist_id | 404 Not Found |
| IT-102 | 存在しない track_id をトラック追加 | 404 Not Found |
| IT-103 | 同一名プレイリスト作成（同セッション） | 409 Conflict |
| IT-104 | 別セッションからのプレイリスト操作 | 403 Forbidden |

### 5. E2E テスト（Playwright）

| TC-ID | シナリオ | 手順 | 確認内容 |
|-------|--------|------|---------|
| E2E-001 | プレイリスト作成フロー | プレイリストタブ → 「+ 新規」 → 名前入力 → 「作成」 | プレイリストカードが一覧に表示される |
| E2E-002 | トラックをプレイリストに追加 | tracks タブ → トラックの「+」ボタン → プレイリスト選択 | プレイリスト詳細にトラックが追加される |
| E2E-003 | プレイリスト再生 | プレイリスト詳細 → 「▶ すべて再生」 | Player がプレイリストモードで起動し1曲目が再生される |
| E2E-004 | トラックスキップ | プレイリスト再生中 → 「次へ」ボタン | 2曲目に切り替わる |
| E2E-005 | 並べ替え | プレイリスト詳細 → ドラッグ&ドロップで順序変更 | 変更後の順序で保存されている（ページリロード後も維持） |
| E2E-006 | プレイリスト削除 | プレイリスト一覧 → [︙] → 「削除」 → ConfirmDialog 確認 | 一覧から消える |
| E2E-007 | お気に入り表示 | likes タブ → リアクション済みトラック確認 | いいねしたトラックが表示される |
| E2E-008 | お気に入りからプレイリスト追加 | likes タブ → 「+」ボタン → プレイリスト選択 | プレイリスト詳細にトラックが追加される |
| E2E-009 | モバイル表示 | 375px 幅でプレイリスト一覧・詳細を確認 | レイアウト崩れなし、スクロール動作正常 |
| E2E-010 | 既存ラジオ機能非影響確認 | radio タブ → チャンネル選択 → ストリーム再生 | プレイリスト機能追加後もラジオが正常動作 |

---

## 受入基準（AC）との対応

| AC-ID | 対応テストケース |
|-------|---------------|
| AC-001 | IT-001 |
| AC-002 | E2E-001（50件作成テスト） |
| AC-003 | UT-104 / IT-103 |
| AC-004 | IT-009 |
| AC-005 | E2E-003, E2E-004 |
| AC-006 | UT-101〜103 / IT-104 |
| AC-007 | IT-006 |
| AC-008 | E2E-010 |
| AC-009 | E2E-007 |
| AC-010 | E2E-009 |

---

## テストデータ設計

### テスト用フィクスチャ

```python
# conftest.py
@pytest.fixture
async def test_session_id():
    return "test-session-" + str(uuid4())

@pytest.fixture
async def test_playlist(db_session, test_session_id):
    playlist = Playlist(
        session_id=test_session_id,
        name="テストプレイリスト"
    )
    db_session.add(playlist)
    await db_session.commit()
    return playlist

@pytest.fixture
async def test_track(db_session):
    # 既存チャンネルに紐づくテストトラック
    ...
```

---

## カバレッジ目標

| テスト種別 | 目標カバレッジ | 計測対象 |
|-----------|------------|---------|
| 単体テスト | 80% 以上 | api/routers/playlists.py |
| 結合テスト | 全 AC をカバー | API エンドポイント全件 |
| E2E テスト | 主要ユーザーシナリオ 10 件 | ブラウザ操作フロー |

---

## テスト実行コマンド

```bash
# 単体・結合テスト
cd /Users/tto/.ttoClaw/workspace/products/ai-music-station
docker compose -f docker-compose.test.yml run --rm api pytest tests/test_playlists.py -v

# E2E テスト
npx playwright test tests/e2e/playlist.spec.ts --reporter=html
```

---

## Gate 5 合格条件

- [ ] 単体テスト全件 PASS
- [ ] 結合テスト全件 PASS（モック禁止、実 DB 使用）
- [ ] E2E テスト全件 PASS
- [ ] カバレッジ 80% 以上
- [ ] 既存テスト（radio, tracks, reactions）が全件 PASS のまま
