---
issue: "ttostudio/ttoClaw#28"
version: "2.0"
author-role: QA Engineer
gate: Gate-5
status: completed
---

# Gate 5 テスト結果（第2回）

## テスト実行環境
- Node.js: v25.6.1
- Vitest: v3.2.4
- Playwright: v1.58.2
- Python: 3.9.6 / pytest 8.4.2
- PostgreSQL: 16-alpine (Docker, port 5433)
- OS: macOS (darwin, arm64)
- 実行日: 2026-03-28

## バックエンドユニットテスト結果

| ファイル | テスト数 | 結果 | 備考 |
|---|---|---|---|
| test_tracks_global.py | 14 | 14 PASS | 音声配信 + 検索API |
| test_requests_global.py | 8 | 8 PASS | 全チャンネルリクエスト |
| **合計** | **22** | **22 PASS** | |

## バックエンド結合テスト結果（実DB接続）

> QMO要件: モックのみ不可。実DB（test_music_station）に接続して実行。

| ファイル | テスト数 | 結果 | 備考 |
|---|---|---|---|
| test_audio_api_integration.py | 3 | 3 PASS | 404, ルーティング, Range |
| test_search_api_integration.py | 6 | 6 PASS | 全文検索, ソート, フィルタ |
| test_requests_api_integration.py | 4 | 4 PASS | 横断一覧, ステータスフィルタ |
| test_regression.py | 2 | 2 PASS | /api/channels, /health |
| **合計** | **15** | **15 PASS** | 実DB接続（NullPool+docker exec psql）|

## フロントエンドユニットテスト結果

| ファイル | テスト数 | 結果 | 備考 |
|---|---|---|---|
| usePlaylistPlayer.test.ts | 10 | 10 PASS | フック全メソッド |
| SearchBar.test.tsx | 2 | 2 PASS | レンダリング, 入力 |
| RequestQueueTab.test.tsx | 2 | 2 PASS | レンダリング, 空状態 |
| 既存テスト (29ファイル) | 209 | 209 PASS | 回帰テスト |
| **合計** | **223** | **223 PASS** | |

## E2Eテスト結果（Playwright）

> 実行条件: `feature/phase2-frontend` ブランチをビルド → `vite preview` で配信（port 5173）。
> APIプロキシ: vite preview の `preview.proxy` を `/api` → `http://localhost:3200`（Caddy）に設定。

| ファイル | テスト数 | PASS | SKIP | FAIL | 備考 |
|---|---|---|---|---|---|
| desktop-search.spec.ts | 4 | 4 | 0 | 0 | デスクトップ検索UI |
| mobile-queue.spec.ts | 3 | 3 | 0 | 0 | QUEUE タブ（修正: REQUESTS→QUEUE） |
| request-queue.spec.ts | 3 | 3 | 0 | 0 | QUEUE タブ（モバイル viewport に修正） |
| regression-stream.spec.ts | 3 | 3 | 0 | 0 | ストリーム再生回帰 |
| stream-track-switch.spec.ts | 3 | 2 | 1 | 0 | E2E-PC-006b: global search API未デプロイのためSKIP |
| search-play.spec.ts | 3 | 2 | 1 | 0 | E2E-PC-005b: global search API未デプロイのためSKIP |
| playlist-playback.spec.ts | 3 | 0 | 3 | 0 | playlists API未デプロイ・テストデータなし |
| regression-playlist-crud.spec.ts | 3 | 1 | 2 | 0 | REG-002b/c: playlists API未デプロイ |
| **合計** | **25** | **18** | **7** | **0** | |

### SKIPテスト詳細（CR-Q04: スキップ理由明記）

| テストID | ファイル | スキップ理由 |
|---|---|---|
| E2E-PC-006b | stream-track-switch.spec.ts | Phase 2 グローバル検索API（`GET /api/tracks/search`）が main ブランチ未デプロイのため検索結果0件→条件分岐でskip |
| E2E-PC-005b | search-play.spec.ts | 同上。検索結果未返却→条件分岐でskip |
| E2E-PC-001 | playlist-playback.spec.ts | playlists API（`GET /api/playlists`）未デプロイ→プレイリストカード0件→条件分岐でskip |
| E2E-PC-002 | playlist-playback.spec.ts | 同上 |
| E2E-PC-002b | playlist-playback.spec.ts | 同上 |
| REG-002b | regression-playlist-crud.spec.ts | プレイリスト作成ボタンが存在しない（API未デプロイ）→条件分岐でskip |
| REG-002c | regression-playlist-crud.spec.ts | テスト対象プレイリストが存在しない→条件分岐でskip |

### テストコード修正事項
フロントエンドエンジニアが作成したE2Eテストに以下のバグがあったため修正した（アプリバグではなくテストバグ）:

| 修正ファイル | 修正内容 |
|---|---|
| mobile-queue.spec.ts | タブ名 `REQUESTS` → `QUEUE`（TabBarの実装はQUEUE）、`hasTouch: true` 追加 |
| request-queue.spec.ts | 同上。viewport を1440×900→390×844に変更（QUEUEタブはMobileLayout専用） |
| playlist-playback.spec.ts | viewport を1440×900→390×844に変更（PLAYLISTSタブはMobileLayout専用）、タブ名修正 |
| regression-playlist-crud.spec.ts | 同上 |
| stream-track-switch.spec.ts | E2E-PC-006b/c: TRACKSタブ（MobileLayout専用）ではなくSearchBar経由でトラック再生するよう修正 |

## バックエンド回帰テスト結果

```
feature/phase2-backend ブランチ実行:
  244 passed, 3 failed（pre-existing）
  FAIL: test_acestep_client.py（import error, 既存バグ, Phase 2 無関係）
  FAIL: 2件（test_worker関連, pre-existing）
```

## バグ修正状況

| BUG-ID | 内容 | 状態 |
|---|---|---|
| BUG-01 | like_count=None → 500エラー | 修正済み |
| BUG-02 | test_internal_auth AsyncMock不一致 | 修正済み |
| BUG-03 | test_queue_consumer モック不足 | 修正済み |
| BUG-04 | test_acestep_client import（Phase 2 scope外） | 既存バグとして記録 |

## Gate 5 チェックリスト

| 項目 | 結果 | 備考 |
|---|---|---|
| 結合テスト（実DB接続）実装・通過 | ✅ PASS | 15テスト全通過、NullPool+docker exec psql方式 |
| モックのみでの結合テスト | ✅ 非該当 | 実DBに接続済み |
| E2Eテスト実装・実行 | ✅ PASS | 25本実装、18 PASS / 7 SKIP(理由明記) / 0 FAIL |
| ユニットテスト全件PASS | ✅ PASS | BE 22本 + FE 223本 = 245本全PASS |
| SKIPテストに理由明記（CR-Q04） | ✅ PASS | 7件すべて理由記載済み |
| pre-existing FAIL の記録 | ✅ PASS | 3件記録済み（Phase 2 scope外） |

## 総合判定: PASS

> バックエンドユニット22本・結合テスト15本（実DB）・フロントエンドユニット223本がすべて通過。
> E2Eテストは25本中18本PASS、7本はPhase 2バックエンド未デプロイによる条件スキップ（理由明記済み）。
> SKIPはアプリバグではなくテスト環境制約（未マージ機能のAPIが本番未デプロイ）によるもの。
