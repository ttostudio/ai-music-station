# テスト設計書 — プレイリスト機能

**バージョン**: 2.0
**作成日**: 2026-03-27
**担当**: QA Engineer
**更新**: 既存テストフレームワーク（pytest + AsyncMock / Vitest + Testing Library）に合わせて詳細化

---

## 1. テスト方針

- **APIテスト（結合テスト）**: pytest + FastAPI TestClient（AsyncMock でセッションをモック）
- **フロントエンドテスト**: Vitest + @testing-library/react
- **E2Eテスト**: Playwright（docker compose 起動環境）
- **実 DB 結合テスト**: `@pytest.mark.integration` マーカー（Gate 5 必須）

---

## 2. テスト環境要件

### バックエンド
| 項目 | 内容 |
|------|------|
| 言語/FW | Python 3.11+, pytest, FastAPI TestClient |
| 非同期 | `pytest-asyncio`（`asyncio_mode = "auto"`） |
| DBモック | `AsyncMock` / `MagicMock`（ユニット・APIテスト） |
| 実 DB | PostgreSQL（`@pytest.mark.integration` テスト） |
| 実行コマンド | `pytest tests/test_playlists_api.py` |

### フロントエンド
| 項目 | 内容 |
|------|------|
| 言語/FW | TypeScript, Vitest, @testing-library/react |
| 環境 | jsdom（`vite.config.ts` の `test.environment`） |
| セットアップ | `frontend/src/test-setup.ts`（matchMedia, ResizeObserver パッチ済） |
| 実行コマンド | `npm run test` |

### E2E
| 項目 | 内容 |
|------|------|
| ツール | Playwright |
| ブラウザ | Chromium（headless） |
| 対象環境 | `http://localhost:3000`（docker compose up 後） |
| 実行コマンド | `npx playwright test frontend/e2e/playlist.spec.ts` |

---

## 3. テストデータ

### バックエンド（`tests/conftest.py` への追加）

```python
SAMPLE_SESSION_ID = "session-abc-001"
SAMPLE_SESSION_ID_OTHER = "session-xyz-999"
SAMPLE_PLAYLIST_ID = uuid.UUID("11111111-1111-1111-1111-111111111111")

@pytest.fixture
def sample_playlist() -> Playlist:
    return Playlist(
        id=SAMPLE_PLAYLIST_ID,
        name="テストプレイリスト",
        description="テスト用の説明文",
        user_id=SAMPLE_SESSION_ID,
        is_public=True,
        created_at=datetime(2026, 3, 27, 12, 0, 0),
        updated_at=datetime(2026, 3, 27, 12, 0, 0),
    )

@pytest.fixture
def sample_playlist_track(sample_playlist, sample_track) -> PlaylistTrack:
    return PlaylistTrack(
        id=uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"),
        playlist_id=sample_playlist.id,
        track_id=sample_track.id,
        position=0,
        added_at=datetime(2026, 3, 27, 12, 0, 0),
    )
```

### フロントエンド（テスト共通定義）

```typescript
export const mockPlaylist = {
  id: "11111111-1111-1111-1111-111111111111",
  name: "テストプレイリスト",
  description: "テスト用の説明文",
  user_id: "session-abc-001",
  is_public: true,
  track_count: 1,
  duration_ms: 180000,
  created_at: "2026-03-27T12:00:00Z",
  updated_at: "2026-03-27T12:00:00Z",
};

export const mockPlaylistTrack = {
  id: "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
  playlist_id: "11111111-1111-1111-1111-111111111111",
  track_id: "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
  position: 0,
  added_at: "2026-03-27T12:00:00Z",
};
```

---

## 4. APIテスト（結合テスト）

**ファイル**: `tests/test_playlists_api.py`

### 4.1 プレイリスト CRUD

| ID | テストケース | 前提条件 | 手順 | 期待結果 |
|----|------------|---------|------|---------|
| API-001 | プレイリスト作成（正常） | DB にプレイリストなし | POST `/api/playlists` `{"name":"マイリスト","description":"説明","user_id":"session-abc-001"}` | 201、`id`(UUID)・`name`・`created_at` を含む JSON 返却。DB に1レコード挿入 |
| API-002 | 名前なしで作成 | — | POST `/api/playlists` `{"description":"..."}` | 422 Unprocessable Entity |
| API-003 | 名前101文字超で作成 | — | POST `/api/playlists` `{"name":"A"*101}` | 422 |
| API-004 | プレイリスト一覧取得（セッション指定） | session-abc-001 のプレイリスト2件、他セッション1件 | GET `/api/playlists?session_id=session-abc-001` | 200、2件のみ返却 |
| API-005 | プレイリスト一覧取得（0件） | セッションにプレイリストなし | GET `/api/playlists?session_id=session-abc-001` | 200、`playlists:[]` |
| API-006 | プレイリスト詳細取得（正常） | プレイリスト1件、トラック2件 | GET `/api/playlists/{id}` | 200、トラックを `position` 昇順で含む |
| API-007 | プレイリスト詳細取得（存在しないID） | — | GET `/api/playlists/00000000-0000-0000-0000-000000000000` | 404 |
| API-008 | プレイリスト更新（正常） | 既存プレイリスト | PATCH `/api/playlists/{id}` `{"name":"新しい名前","session_id":"session-abc-001"}` | 200、`name` が更新済み |
| API-009 | プレイリスト更新（他セッション） | 他セッションのプレイリスト | PATCH `/api/playlists/{id}` `{"session_id":"session-xyz-999"}` | 403 Forbidden |
| API-010 | プレイリスト削除（正常） | 既存プレイリスト + 関連 playlist_tracks 2件 | DELETE `/api/playlists/{id}?session_id=session-abc-001` | 204、プレイリスト削除、playlist_tracks も CASCADE 削除 |
| API-011 | プレイリスト削除（他セッション） | — | DELETE `/api/playlists/{id}?session_id=session-xyz-999` | 403 |
| API-012 | プレイリスト削除（存在しないID） | — | DELETE `/api/playlists/00000000-...` | 404 |

### 4.2 トラック追加/削除/並べ替え

| ID | テストケース | 前提条件 | 手順 | 期待結果 |
|----|------------|---------|------|---------|
| API-020 | トラック追加（正常） | プレイリスト存在、トラック存在 | POST `/api/playlists/{id}/tracks` `{"track_id":"...","session_id":"..."}` | 201、`position` が既存最大+1 |
| API-021 | トラック追加（重複） | 同トラックが追加済み | 同一 track_id で再度 POST | 409 Conflict |
| API-022 | トラック追加（存在しないトラックID） | — | POST `{"track_id":"00000000-..."}` | 404 |
| API-023 | トラック追加（他セッション） | 他セッションのプレイリスト | POST `{"session_id":"session-xyz-999"}` | 403 |
| API-024 | トラック削除（正常） | プレイリストにトラック2件 | DELETE `/api/playlists/{id}/tracks/{track_id}?session_id=...` | 204、残り1件の `position` が 0 に再採番 |
| API-025 | トラック削除（存在しないトラック） | — | DELETE `/api/playlists/{id}/tracks/00000000-...` | 404 |
| API-026 | 並べ替え（正常） | トラック3件（position: 0,1,2） | PUT `/api/playlists/{id}/tracks/reorder` `{"order":["id2","id0","id1"]}` | 200、GET で position 0=id2, 1=id0, 2=id1 の順 |
| API-027 | 並べ替え（不完全な ID リスト） | トラック3件 | `order` に2件のみ送信 | 422 |
| API-028 | 並べ替え（他セッション） | — | PUT with `session_id=session-xyz-999` | 403 |

### 4.3 ページネーション

| ID | テストケース | 前提条件 | 手順 | 期待結果 |
|----|------------|---------|------|---------|
| API-030 | プレイリスト一覧ページネーション | 25件 | GET `...?limit=10&offset=0` | 200、10件、`total=25`、`has_next=true` |
| API-031 | プレイリスト最終ページ | 25件 | GET `...?limit=10&offset=20` | 200、5件、`has_next=false` |
| API-032 | 上限200件のトラック取得 | トラック200件 | GET `/api/playlists/{id}` | 200、200件全て返却 |
| API-033 | 上限201件目のトラック追加 | 200件追加済み | POST `/api/playlists/{id}/tracks` | 400 上限超過エラー |

### 4.4 お気に入りトラック

| ID | テストケース | 前提条件 | 手順 | 期待結果 |
|----|------------|---------|------|---------|
| API-040 | お気に入り一覧取得（正常） | session-abc-001 が3件 like | GET `/api/favorites?session_id=session-abc-001` | 200、3件返却 |
| API-041 | お気に入り一覧取得（0件） | like なし | GET `/api/favorites?session_id=session-abc-001` | 200、空配列 |

---

## 5. バックエンド ユニットテスト

**ファイル**: `tests/test_playlists_unit.py`

| ID | テストケース | 対象 | 期待結果 |
|----|------------|------|---------|
| UNIT-001 | position 再採番ロジック（削除後） | ヘルパー関数 | position 0,1,2 から 1 を削除 → 0,1 に詰める |
| UNIT-002 | position 付与ロジック（追加時） | ヘルパー関数 | 既存 max position + 1 を返す（空の場合 0） |
| UNIT-003 | セッションID 一致チェック（一致） | 権限チェック関数 | True を返す |
| UNIT-004 | セッションID 一致チェック（不一致） | 権限チェック関数 | False を返す |

---

## 6. フロントエンド コンポーネントテスト（Vitest）

### 6.1 PlaylistList
**ファイル**: `frontend/src/__tests__/PlaylistList.test.tsx`

| ID | テストケース | 手順 | 期待結果 |
|----|------------|------|---------|
| FE-001 | プレイリスト一覧が表示される | `render(<PlaylistList playlists={[mockPlaylist]} />)` | 「テストプレイリスト」が画面に表示 |
| FE-002 | 0件時の空状態表示 | `render(<PlaylistList playlists={[]} />)` | 空状態メッセージを表示 |
| FE-003 | [+] ボタンクリックでモーダル表示 | [+] ボタンをクリック | `PlaylistCreateModal` が表示される |

### 6.2 PlaylistCreateModal
**ファイル**: `frontend/src/__tests__/PlaylistCreateModal.test.tsx`

| ID | テストケース | 手順 | 期待結果 |
|----|------------|------|---------|
| FE-010 | 名前入力して作成 | 名前欄に「新しいリスト」入力 → [作成する] クリック | `onSubmit({name:"新しいリスト"})` が呼ばれる |
| FE-011 | 名前が空の場合 submit 無効 | 名前欄が空のまま [作成する] クリック | ボタンが disabled またはエラーメッセージ表示 |
| FE-012 | キャンセルでモーダルが閉じる | [キャンセル] クリック | `onClose` コールバックが呼ばれる |
| FE-013 | 名前50文字制限 | 51文字入力 | 50文字でトリミングまたはバリデーションエラー表示 |

### 6.3 PlaylistDetail
**ファイル**: `frontend/src/__tests__/PlaylistDetail.test.tsx`

| ID | テストケース | 手順 | 期待結果 |
|----|------------|------|---------|
| FE-020 | トラック一覧が position 順で表示 | `render(<PlaylistDetail tracks={[pos2, pos0, pos1]} />)` | 表示順が position 昇順と一致 |
| FE-021 | [▶ すべて再生] クリックで再生コールバック | [▶ すべて再生] クリック | `onPlay` コールバックが呼ばれる |
| FE-022 | トラック行の削除ボタン | [✕] クリック | 削除コールバックが呼ばれる |
| FE-023 | [← 戻る] クリックで一覧に戻る | [← 戻る] クリック | `onBack` コールバックが呼ばれる |

### 6.4 PlaylistCard
**ファイル**: `frontend/src/__tests__/PlaylistCard.test.tsx`

| ID | テストケース | 手順 | 期待結果 |
|----|------------|------|---------|
| FE-030 | 名前・曲数・時間が表示される | `render(<PlaylistCard playlist={{...track_count:3, duration_ms:540000}} />)` | 「テストプレイリスト」「3曲」「9:00」が表示 |
| FE-031 | クリックで onSelect が呼ばれる | カードをクリック | `onSelect(mockPlaylist)` が呼ばれる |

### 6.5 TrackSelectModal
**ファイル**: `frontend/src/__tests__/TrackSelectModal.test.tsx`

| ID | テストケース | 手順 | 期待結果 |
|----|------------|------|---------|
| FE-040 | トラック一覧が表示される | API モック3件で `render(<TrackSelectModal />)` | 3件のトラック名が表示 |
| FE-041 | 既追加トラックはグレーアウト | `addedTrackIds` に track_id を渡す | 追加済み行がグレーアウト・チェックボックス disabled |
| FE-042 | 選択後 [追加する] で onAdd 呼出 | チェックボックスを1件選択 → [追加する] クリック | `onAdd([track_id])` が呼ばれる |
| FE-043 | 検索フィルタが効く | 3件中1件のみ「夕暮れ」を含む状態で「夕暮れ」入力 | 1件のみ表示 |

### 6.6 TabBar（既存ファイルへの追加）
**ファイル**: `frontend/src/__tests__/TabBar.test.tsx`

| ID | テストケース | 期待結果 |
|----|------------|---------|
| FE-050 | 「PLAYLISTS」タブが表示される | `screen.getByText("PLAYLISTS")` が存在 |
| FE-051 | PLAYLISTSタブクリックで onChange("playlist") が呼ばれる | `onChange` が `"playlist"` で呼ばれる |

---

## 7. フロントエンド 統合テスト

**ファイル**: `frontend/src/__tests__/integration/PlaylistFlow.test.tsx`

| ID | テストケース | 手順 | 期待結果 |
|----|------------|------|---------|
| INT-001 | 作成→一覧への反映 | [+] クリック → 名前入力 → 送信 | 一覧に新しいプレイリスト名が表示 |
| INT-002 | 一覧→詳細→一覧の往復 | カードクリック → [← 戻る] クリック | 一覧画面に戻る |
| INT-003 | 削除後一覧から消える | 詳細画面で削除 → 一覧に戻る | 削除したプレイリストが消える |

---

## 8. E2Eテスト（Playwright）

**ファイル**: `frontend/e2e/playlist.spec.ts`（新規作成）

受入基準（requirements.md AC-001〜010）との対応:

| E2E ID | AC ID | テストケース | 前提条件 | 手順 | 期待結果 |
|--------|-------|------------|---------|------|---------|
| E2E-001 | AC-001 | プレイリスト作成 | アプリ起動済み | ① PLAYLISTSタブ ② [+] ③ 名前「夕焼けリスト」入力 ④ [作成する] | 一覧に「夕焼けリスト」が表示される |
| E2E-002 | AC-002, AC-005 | プレイリスト作成→トラック追加→再生 | トラック1件以上存在 | ① プレイリスト作成 ② [+ トラックを追加] ③ トラック選択 ④ [▶ すべて再生] | Player が playlist モードで選択トラックを再生 |
| E2E-003 | AC-003 | 重複トラック追加は弾かれる | トラック追加済みプレイリスト | 同一トラックを再度追加 | エラー表示または追加ボタン disabled |
| E2E-004 | AC-004 | 並べ替え後の順序保持 | トラック3件のプレイリスト | ドラッグ&ドロップで順序変更 → ページリロード | リロード後も変更後の順序が保持される |
| E2E-005 | AC-006 | 他セッションからの操作は403 | 別セッションIDのプレイリスト | 直接 API を呼び出して更新試行 | 403 エラー（UIでは操作不可） |
| E2E-006 | AC-007 | プレイリスト削除で関連トラックも削除 | プレイリスト + トラック2件 | プレイリストを削除 | 一覧から消える。直接 GET で 404 |
| E2E-007 | AC-008 | 既存ラジオ機能への影響なし | — | ① RADIOタブで再生 ② PLAYLISTSタブに切替 ③ RADIOタブに戻る | ラジオ再生が継続している |
| E2E-008 | AC-009 | お気に入りトラック表示 | トラックに like リアクション1件 | FAVORITESまたは対象タブを確認 | like したトラックが表示される |
| E2E-009 | AC-010 | モバイル（375px）でのプレイリスト操作 | ビューポート 375×667 | プレイリスト作成→トラック追加→削除 | 各操作が正常。スクリーンショットで UI 崩れなし確認 |
| E2E-010 | — | タブレット横（1024px）での表示 | ビューポート 1024×768 | プレイリスト詳細を開く | サイドパネルとして表示、ラジオと共存 |
| E2E-011 | — | 説明文なしでのプレイリスト作成 | — | 名前のみ入力して作成 | 正常に作成（description は null） |
| E2E-012 | — | プレイリスト編集（名前変更） | 既存プレイリスト | 編集ボタン → 名前変更 → 保存 | 変更した名前が一覧に反映 |

---

## 9. テストファイル構成（実装時）

```
tests/
├── conftest.py                           # Playlist / PlaylistTrack fixtures 追加
├── test_playlists_api.py                 # 4.1〜4.4 APIテスト（AsyncMock + TestClient）
└── test_playlists_unit.py                # 5. ユニットテスト

frontend/src/__tests__/
├── PlaylistList.test.tsx                 # FE-001〜003
├── PlaylistCreateModal.test.tsx          # FE-010〜013
├── PlaylistDetail.test.tsx               # FE-020〜023
├── PlaylistCard.test.tsx                 # FE-030〜031
├── TrackSelectModal.test.tsx             # FE-040〜043
├── TabBar.test.tsx                       # 既存 + FE-050〜051
└── integration/
    └── PlaylistFlow.test.tsx             # INT-001〜003

frontend/e2e/
└── playlist.spec.ts                      # E2E-001〜012
```

---

## 10. テスト優先度

| 優先度 | テストID | 理由 |
|--------|---------|------|
| P0（必須） | API-001〜012, API-020〜028 | コア CRUD + 権限チェック |
| P0（必須） | E2E-001, E2E-002 | 主要シナリオ（作成→再生）の一貫動作確認 |
| P1（重要） | FE-001〜051 | コンポーネント単体の正しさ |
| P1（重要） | E2E-003〜009 | AC 直接対応 |
| P2（追加） | API-030〜041, INT-001〜003, E2E-010〜012 | エッジケース・ページネーション・マルチ端末 |

---

## 11. Gate 5 合格基準

| 項目 | 基準 |
|------|------|
| ユニット・APIテスト | 全件 PASS |
| フロントエンドテスト | 全件 PASS |
| 結合テスト | 実 DB 接続で全件 PASS（`AsyncMock` のみは不合格） |
| E2Eテスト | P0/P1 全件 PASS |
| skip テスト | `pytest.mark.skip(reason="...")` または `it.skip("...")` で理由を明記 |
| カバレッジ | プレイリスト関連モジュール 80%以上 |

---

## 参考ドキュメント

- `docs/sdd/playlist-feature/requirements.md` — 機能要件・受入基準（AC-001〜010）
- `docs/sdd/playlist-feature/db-design.md` — DBスキーマ・APIエンドポイント仕様
- `docs/sdd/playlist-feature/ui-design.md` — コンポーネント・デザイントークン
- `tests/conftest.py` — 既存 fixtures（sample_channel, sample_track）のパターン参考
- `tests/test_api_requests.py` — AsyncMock + TestClient パターン参考
- `frontend/src/__tests__/App.test.tsx` — Vitest コンポーネントテストパターン参考
