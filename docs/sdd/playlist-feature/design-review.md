---
reviewer-role: Design Reviewer（独立レビュー）
gate: Gate-2
reviewed-at: 2026-03-27
status: conditional-pass
---

# 設計レビュー結果 — プレイリスト機能

> **注記**: 本ファイルには以前 CEO 代行による暫定 PASS 判定が記載されていたが、独立レビュアーによる精査の結果、複数の Critical/Major 指摘が見つかったため差し替える。

## 総合判定: **Conditional Pass**

Critical 1件・Major 5件の修正を条件とする。いずれもドキュメント間の転記ミス・命名不整合であり、修正コストは低い。修正完了後、再レビューなしで実装着手可。

---

## 各ドキュメント評価

| ドキュメント | 判定 | コメント |
|------------|------|---------|
| requirements.md | **Pass** | FR/NFR の粒度・スコープ・AC 記述ともに適切 |
| api-spec.md | **Conditional** | DR-002〜006 の修正必要 |
| db-design.md | **Conditional** | DR-001（命名）・DR-007・DR-009 の修正必要 |
| ui-design.md | **Conditional** | DR-003・DR-005 の修正必要 |
| test-design.md | **Conditional** | DR-002・DR-004・DR-008 の修正必要 |

---

## 指摘事項一覧

### Critical

#### DR-001: DB カラム名 `user_id` と API フィールド名 `session_id` の不一致

- **対象**: db-design.md ↔ api-spec.md
- **内容**: DB テーブル `playlists` のカラム名は `user_id`（db-design.md）だが、API レスポンス（POST /api/playlists）・requirements.md・api-spec.md 全体では `session_id` で統一されている。実装者が DB カラム名とアプリレイヤーのフィールド名のどちらに合わせるか迷い、コードレビュー時も混乱を招く。
- **修正**: db-design.md・Alembic マイグレーション・SQLAlchemy モデルのカラム名を `user_id` → `session_id` に統一する

---

### Major

#### DR-002: DELETE レスポンスのステータスコード不一致（200 vs 204）

- **対象**: api-spec.md ↔ test-design.md（API-010, API-023）
- **内容**: api-spec.md では `DELETE /api/playlists/{id}` と `DELETE .../tracks/{track_id}` ともに `200 OK`（レスポンスボディあり）。test-design.md の API-010・API-023 では期待結果 `204`。このままテストを実装すると必ず失敗する。
- **修正**: どちらかに統一。api-spec.md の `200 OK` を正とし test-design.md を修正する（推奨）。またはどちらも `204 No Content` に統一しボディを省略する。

#### DR-003: name・description のバリデーション上限値が UI 設計と API 仕様で異なる

- **対象**: ui-design.md（3.3節バリデーション） ↔ api-spec.md（POST /api/playlists）
- **内容**:
  - ui-design.md: name 最大 **50文字**、description 最大 **200文字**
  - api-spec.md: name 1〜**100文字**、description 最大 **500文字**
  - UI が 50 文字で弾くのに API は 100 文字まで受け付ける（またはその逆）という矛盾が生じる。
- **修正**: api-spec.md を正とし（name 100文字、description 500文字）、ui-design.md のバリデーション値を合わせる

#### DR-004: トラック追加リクエストフィールド名 `track_id`（単数）vs `track_ids`（複数）の不一致

- **対象**: api-spec.md（POST .../tracks） ↔ test-design.md（API-020, API-031）
- **内容**: api-spec.md では `{ "track_id": "uuid" }` — 1件ずつ追加。test-design.md では `{ track_ids }` — 複数件を想定。UI設計のトラック追加モーダルでは複数チェックボックスから一括追加するため、複数形の方が UX に合っている。
- **修正**: api-spec.md を `track_ids: string[]` に変更し、test-design.md・UI設計と整合させる

#### DR-005: reorder エンドポイントのパス・メソッドが UI 設計と API 仕様で異なる

- **対象**: api-spec.md ↔ ui-design.md（6.3節）
- **内容**:
  - api-spec.md: `PUT /api/playlists/{id}/tracks/reorder`
  - ui-design.md 6.3節: `PATCH /api/playlists/:id/tracks/order`（メソッドも異なる）
- **修正**: api-spec.md を正とし（`PUT .../tracks/reorder`）、ui-design.md を修正する

#### DR-006: 既存 `TrackResponse` スキーマにないフィールドを API 仕様が返却している

- **対象**: api-spec.md ↔ 既存 `api/schemas.py:TrackResponse`
- **内容**: api-spec.md（GET /api/playlists/{id}）のトラック詳細レスポンスに `quality_score`・`channel_id` フィールドを含むが、既存の `schemas.py:TrackResponse` にこれらの定義がない（`quality_score` は `TrackQualityResponse` にあるが `TrackResponse` にはない）。Backend Engineer がそのまま既存スキーマを流用するとフィールドが欠落してテストが失敗する。
- **修正**: api-spec.md または api-design.md に `PlaylistTrackResponse`（`quality_score: float | None`・`channel_id: uuid | None` 追加）を明示的に定義する。あるいは既存 `TrackResponse` を拡張する方針を記載する

---

### Minor

#### DR-007: `is_public` カラムが DB にあるが API・要件に記載なし

- **対象**: db-design.md
- **内容**: requirements.md のスコープ外に「プレイリストの公開・共有機能」と明記されているにもかかわらず、DB テーブルには `is_public BOOLEAN default=true` が定義されている。API から操作するエンドポイントがなく、このカラムは現フェーズで使われない。
- **対応**: db-design.md の設計判断セクションに「将来の公開機能拡張のための予約カラム。現フェーズでは API からは操作しない」と明記する

#### DR-008: トラック上限超過のエラーコード不一致（422 vs 400）

- **対象**: api-spec.md（POST .../tracks エラー表） ↔ test-design.md（API-027）
- **内容**: api-spec.md では `422`、test-design.md（API-027）では `400`
- **対応**: FastAPI の慣習に合わせ `422` に統一し test-design.md を修正する

#### DR-009: SQLAlchemy モデルの `updated_at` に `onupdate` 未定義

- **対象**: db-design.md（SQLAlchemy モデル参考実装）
- **内容**: `Playlist.updated_at` カラムに `onupdate=func.now()` が記述されていない。PATCH 時に `updated_at` が自動更新されない実装になる恐れがある。
- **対応**: モデル定義に `onupdate=func.now()` を追加するか、アプリケーションコードで明示的に更新する方針を記載する

---

## ポジティブ所見

- **requirements.md**: FR/NFR の粒度が適切で受入基準（AC）がテスト可能な形式で記述されている。スコープの In/Out が明確。
- **db-design.md**: インデックス戦略・並行性制御・カスケード削除の設計判断が具体的に記載されており、高品質。
- **ui-design.md（DR-G2-01 クリア）**: デザイントークンが既存 `styles.css` と照合済みと明記されており、実装時のトークン乖離リスクが低い。ブレークポイント値も `useBreakpoint.ts` と整合。
- **test-design.md**: APIテスト・フロントエンドテスト・E2Eテストの三層が揃っており、Gate 5 でのモックのみテストリスクが低い。

---

## 修正優先度まとめ

| ID | Severity | 対象 | 実装前に必要 |
|----|----------|------|------------|
| DR-001 | Critical | db-design.md / api-spec.md | **必須** |
| DR-002 | Major | api-spec.md / test-design.md | **必須** |
| DR-003 | Major | ui-design.md / api-spec.md | **必須** |
| DR-004 | Major | api-spec.md / test-design.md | **必須** |
| DR-005 | Major | ui-design.md | **必須** |
| DR-006 | Major | api-spec.md | **必須** |
| DR-007 | Minor | db-design.md | 推奨 |
| DR-008 | Minor | test-design.md | 推奨 |
| DR-009 | Minor | db-design.md | 推奨 |

---

Critical 1件・Major 5件の修正完了後、Design Reviewer の再確認なく Backend/Frontend Engineer は実装着手可。
