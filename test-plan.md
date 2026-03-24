# AI Music Station — テスト仕様書（共有機能）

## 1. テスト概要

### 1.1 対象機能
トラック共有機能：共有リンク生成 → OGP対応 → アナリティクストラッキング

| 機能 | 説明 |
|------|------|
| Share API | トラック毎に一意の共有リンク生成 |
| Share Page | OGPメタタグ（title, description, image）対応の共有ページ |
| Tracking API | 共有リンク経由のアクセスと再生を記録 |
| Share Button | フロントエンド「共有」ボタン |

### 1.2 テストスコープ

#### ✅ テスト対象
- 共有リンク生成API (`POST /api/tracks/{id}/share`)
- 共有ページ表示 (`GET /share/{share_token}`)
- トラッキングAPI (`POST /api/tracking/share-access`, `POST /api/tracking/play`)
- フロントエンド共有ボタン UI

#### ❌ スコープ外
- SNS 投稿（共有リンクのプレビュー確認は別タスク）
- メール送信
- QR コード生成

---

## 2. テストケース

### 2.1 共有リンク生成 API テスト

#### TC-001: 正常系 — トラック共有リンク生成
```
前提: 完了済みトラック（track_id）が存在すること
実行: POST /api/tracks/{track_id}/share
期待:
  - 201 Created
  - レスポンス: { share_token, share_url, expires_at, created_at }
  - share_token は URL セーフな base62 エンコード（例: "abc123XyZ"）
  - share_token は一意（同一トラックで複数回呼び出しても同じトークン返却）
```

#### TC-002: エラー系 — 存在しないトラック
```
実行: POST /api/tracks/{invalid_track_id}/share
期待: 404 Not Found, { error: "Track not found" }
```

#### TC-003: エラー系 — 削除済みトラック
```
前提: 削除済みトラック
実行: POST /api/tracks/{deleted_track_id}/share
期待: 404 Not Found
```

#### TC-004: 既存トークンの再使用
```
前提: TC-001 で生成した share_token が存在
実行1: POST /api/tracks/{track_id}/share → token_A
実行2: POST /api/tracks/{track_id}/share → token_B
期待: token_A == token_B（冪等性）
```

---

### 2.2 共有ページ表示 テスト

#### TC-005: 正常系 — 共有ページアクセス + OGP
```
前提: 有効な share_token が存在
実行: GET /share/{share_token}
期待:
  - 200 OK
  - HTML レスポンス
  - OGP メタタグ:
    • og:title = トラック名
    • og:description = "チャンネル: {channel}, BPM: {bpm}, Key: {key}"
    • og:image = トラックのサムネイル (生成方法は別定義)
    • og:url = https://domain/share/{share_token}
```

#### TC-006: 正常系 — トラッキングイベント発火
```
前提: TC-005 と同じ
実行: GET /share/{share_token}
期待:
  - レスポンス 200
  - DB の tracking テーブルに record 作成: { share_token, event: "page_view", user_agent, referer, created_at }
```

#### TC-007: エラー系 — 無効な share_token
```
実行: GET /share/{invalid_token}
期待: 404 Not Found, メッセージ "Shared track not found"
```

#### TC-008: エラー系 — 期限切れ share_token
```
前提: expires_at < now() な share_token
実行: GET /share/{expired_token}
期待: 410 Gone, メッセージ "Shared track has expired"
```

---

### 2.3 トラッキング API テスト

#### TC-009: 共有ページからの再生トラッキング
```
前提: 有効な share_token で共有ページにアクセス
実行: POST /api/tracking/share-access
  Body: { share_token, timestamp }
期待:
  - 200 OK
  - tracking テーブルに記録
```

#### TC-010: 重複トラッキング防止
```
前提: 同一セッション
実行1: POST /api/tracking/share-access { share_token }
実行2: POST /api/tracking/share-access { share_token } (5秒以内)
期待:
  - 両者 200 OK
  - DB に 2 レコード作成（重複排除なし、全て記録）
```

---

### 2.4 フロントエンド UI テスト

#### TC-011: 共有ボタン表示
```
前提: 再生中トラック
実行: TrackHistory 内の各トラックに「共有」アイコン表示
期待:
  - アイコン表示
  - ホバーで "Share track" ツールチップ
```

#### TC-012: 共有ボタンクリック → リンク生成フロー
```
実行: 「共有」ボタンクリック
期待:
  1. API 呼び出し: POST /api/tracks/{id}/share
  2. モーダル表示: { share_url, QRコード（オプション）, コピーボタン }
  3. コピーボタンクリック → クリップボード登録
  4. "Copied to clipboard" トースト表示
```

---

## 3. 結合テスト実装方針

### 3.1 テスト環境
- **DB**: 実 PostgreSQL（Docker Compose）
- **API**: FastAPI @ `http://localhost:8000`
- **テストスクリプト**: Python pytest + httpx

### 3.2 テスト実装
```
tests/
├── integration/
│   ├── conftest.py  (fixtures: db_session, api_client, test_track)
│   └── test_share_api.py
│       ├── test_create_share_link()
│       ├── test_share_page_with_ogp()
│       ├── test_tracking_events()
│       └── test_share_token_expiry()
```

### 3.3 実装例
```python
# tests/integration/test_share_api.py
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_create_share_link(api_client, test_track):
    """TC-001: 共有リンク生成"""
    resp = await api_client.post(f"/api/tracks/{test_track.id}/share")
    assert resp.status_code == 201
    data = resp.json()
    assert "share_token" in data
    assert "share_url" in data
    assert "expires_at" in data

@pytest.mark.asyncio
async def test_share_page_with_ogp(api_client, test_track):
    """TC-005: OGPメタタグ確認"""
    share = await api_client.post(f"/api/tracks/{test_track.id}/share")
    token = share.json()["share_token"]

    resp = await api_client.get(f"/share/{token}")
    assert resp.status_code == 200
    html = resp.text
    assert f"og:title" in html
    assert f"og:image" in html
    assert test_track.title in html
```

### 3.4 テスト実行
```bash
cd /Users/tto/.ttoClaw/workspace/products/ai-music-station
docker-compose up -d postgres api
pytest tests/integration/test_share_api.py -v
```

---

## 4. E2E テスト（Playwright）

### 4.1 テストシナリオ

#### E2E-001: ユーザーが共有ボタンをクリックして URL をコピー
```
1. フロントエンドロード
2. トラック一覧で再生中トラック確認
3. 「共有」ボタンクリック
4. モーダル表示確認
5. 「Copy」ボタンクリック
6. クリップボード確認
```

#### E2E-002: 別ユーザーが共有リンク にアクセス
```
1. 共有リンク を新規ブラウザで開く
2. OGP メタデータ確認（DevTools）
3. ページ表示確認（トラック情報表示）
4. トラッキングイベント確認（DB/API）
```

### 4.2 実装
```
tests/e2e/
└── share.spec.ts
    ├── test("Share button opens modal")
    ├── test("Copy to clipboard works")
    └── test("Shared page displays with OGP")
```

---

## 5. テスト結果判定基準

| 結果 | 判定 | 定義 |
|------|------|------|
| **PASS** | ✅ | 全テストケース成功 + トラッキング記録確認 + E2E動作確認 |
| **FAIL** | ❌ | いずれかのテストケース失敗 |
| **BLOCK** | ⚠️ | API/DB が起動しない、またはテスト環境が整わない |

### 5.1 合格基準
- TC-001 ～ TC-012: 全て成功
- 結合テスト: トラッキング DB に 5件以上のレコード確認
- E2E テスト: 2シナリオ成功
- バグなし（既知バグがあれば別途追跡）

---

## 6. テスト実行記録

### 実行日時: [記入]

| テストID | 結果 | 備考 |
|---------|------|------|
| TC-001 | — | |
| TC-002 | — | |
| TC-005 | — | |
| TC-006 | — | |
| 結合テスト整体 | — | |
| E2E 全体 | — | |

### 発見バグ

| ID | 概要 | 重大度 | 対処 |
|----|------|--------|------|
| — | — | — | |

### サイン
- QA Engineer:
- レビュー日:

