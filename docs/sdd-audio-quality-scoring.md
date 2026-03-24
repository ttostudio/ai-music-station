# SDD: 音響品質スコアリングシステム（Issue #626）

## 1. 概要

生成された楽曲の品質を ffprobe/ffmpeg で客観的に評価し、スコア化する。
スコアは再生リスト優先順位・自動リタイア判定・ダッシュボード表示に活用する。

---

## 2. 音響特徴量リスト

### 2.1 ffprobe で取得するメタデータ

| 特徴量 | コマンド引数 | 用途 |
|--------|------------|------|
| `duration_sec` | `streams[0].duration` | 楽曲長さ判定 |
| `bitrate_kbps` | `format.bit_rate / 1000` | エンコード品質 |
| `sample_rate` | `streams[0].sample_rate` | 音質確認 |
| `channels` | `streams[0].channels` | モノ/ステレオ判定 |
| `file_size_bytes` | `format.size` | ファイル整合性確認 |
| `codec_name` | `streams[0].codec_name` | フォーマット確認 |

```bash
ffprobe -v quiet -print_format json -show_format -show_streams input.flac
```

### 2.2 ffmpeg フィルターで取得する音響特徴量

#### silencedetect（無音検出）
```bash
ffmpeg -i input.flac -af silencedetect=noise=-40dB:duration=1.0 -f null - 2>&1
```
| 特徴量 | 説明 |
|--------|------|
| `silence_duration_sec` | 総無音時間（秒） |
| `silence_ratio` | 無音率 = silence_duration / total_duration（0.0〜1.0） |
| `silence_count` | 無音セグメント数 |

#### volumedetect（音量分析）
```bash
ffmpeg -i input.flac -af volumedetect -f null - 2>&1
```
| 特徴量 | 説明 |
|--------|------|
| `mean_volume_db` | 平均音量（dBFS） 例: -20.5 |
| `max_volume_db` | ピーク音量（dBFS） 例: -3.2 |

#### astats（音響統計）
```bash
ffmpeg -i input.flac -af astats=metadata=1:reset=1 -f null - 2>&1
```
| 特徴量 | 説明 |
|--------|------|
| `crest_factor_db` | ピーク/RMS比（dB）。動的レンジの指標 |
| `flat_factor` | フラット係数。ノイズ・静的音検出 |
| `rms_level_db` | RMS音量（dBFS） |

---

## 3. スコアリングロジック

### 3.1 個別スコア計算（各 0〜100）

#### duration_score（重み: 20%）
```
duration_sec < 60:   0
60 ≤ duration < 120:  score = (duration - 60) / 60 * 60       (0→60)
120 ≤ duration ≤ 240: score = 100                               (最適範囲)
240 < duration ≤ 360: score = 100 - (duration - 240) / 120 * 30 (100→70)
duration > 360:       score = max(0, 70 - (duration - 360) / 60 * 10)
```

#### silence_score（重み: 25%）
```
silence_ratio < 0.02:  score = 100
0.02 ≤ ratio < 0.10:   score = 100 - (ratio - 0.02) / 0.08 * 20  (100→80)
0.10 ≤ ratio < 0.25:   score = 80 - (ratio - 0.10) / 0.15 * 50   (80→30)
0.25 ≤ ratio < 0.50:   score = 30 - (ratio - 0.25) / 0.25 * 30   (30→0)
ratio ≥ 0.50:          score = 0
```

#### volume_score（重み: 20%）
```
mean_volume_db の理想範囲: -22dB 〜 -10dB
mean < -40:  score = 0  (無音に近い)
-40 ≤ mean < -22: score = (mean + 40) / 18 * 60  (0→60)
-22 ≤ mean ≤ -10: score = 100  (理想)
-10 < mean ≤ -3:  score = 100 - (mean + 10) / 7 * 40  (100→60)
mean > -3:        score = max(0, 60 - (mean + 3) * 20)  (クリッピング懸念)
```

#### bitrate_score（重み: 15%）
```
FLAC は可逆圧縮なので bitrate_kbps はソース品質を反映
bitrate ≥ 900:  score = 100
600 ≤ bitrate < 900: score = 60 + (bitrate - 600) / 300 * 40
300 ≤ bitrate < 600: score = 20 + (bitrate - 300) / 300 * 40
bitrate < 300:  score = 0
```

#### dynamic_score（重み: 20%）
```
crest_factor_db（動的レンジ）の理想: 8〜20dB
crest < 4:        score = 0  (完全に圧縮/フラット)
4 ≤ crest < 8:   score = (crest - 4) / 4 * 50  (0→50)
8 ≤ crest ≤ 20:  score = 100  (理想)
crest > 20:       score = 100 - (crest - 20) / 10 * 20  (過剰ダイナミクス)
```

### 3.2 overall_score（総合スコア）
```
overall_score = (
    duration_score * 0.20 +
    silence_score  * 0.25 +
    volume_score   * 0.20 +
    bitrate_score  * 0.15 +
    dynamic_score  * 0.20
)
```

### 3.3 品質グレード
| スコア範囲 | グレード | 説明 |
|-----------|---------|------|
| 80〜100 | A | 高品質。プレイリスト優先表示 |
| 60〜79 | B | 標準品質 |
| 40〜59 | C | 要改善。次期生成の参考に |
| 0〜39 | D | 低品質。自動リタイア候補 |

---

## 4. DB設計

### 4.1 新規テーブル: `track_quality_scores`

```sql
CREATE TABLE track_quality_scores (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    track_id        UUID NOT NULL UNIQUE REFERENCES tracks(id) ON DELETE CASCADE,

    -- ffprobe メタデータ
    duration_sec    FLOAT,
    bitrate_kbps    INTEGER,
    sample_rate     INTEGER,
    channels        INTEGER,
    file_size_bytes BIGINT,
    codec_name      VARCHAR(32),

    -- 無音分析
    silence_duration_sec  FLOAT,
    silence_ratio         FLOAT,
    silence_count         INTEGER,

    -- 音量分析
    mean_volume_db  FLOAT,
    max_volume_db   FLOAT,
    rms_level_db    FLOAT,

    -- 動的レンジ
    crest_factor_db FLOAT,
    flat_factor     FLOAT,

    -- 個別スコア (0〜100)
    duration_score  FLOAT,
    silence_score   FLOAT,
    volume_score    FLOAT,
    bitrate_score   FLOAT,
    dynamic_score   FLOAT,

    -- 総合スコア・グレード
    overall_score   FLOAT,
    grade           VARCHAR(1),      -- A/B/C/D

    -- 管理フィールド
    analysis_version INTEGER NOT NULL DEFAULT 1,
    analyzed_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    error_message   TEXT,            -- 分析失敗時のみ
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- インデックス
CREATE INDEX idx_track_quality_track    ON track_quality_scores(track_id);
CREATE INDEX idx_track_quality_overall  ON track_quality_scores(overall_score DESC NULLS LAST);
CREATE INDEX idx_track_quality_analyzed ON track_quality_scores(analyzed_at DESC);
CREATE INDEX idx_track_quality_grade    ON track_quality_scores(grade);
```

### 4.2 既存テーブルへの変更
なし（`track_quality_scores` は完全に独立したテーブルとして設計し、tracks テーブルは変更しない）

---

## 5. ワーカー統合方式

### 5.1 設計方針
**生成後フック方式**を採用。`queue_consumer.py` の `process_request()` でトラック作成後、非同期で品質分析を起動する。

理由:
- 生成が完了した直後に分析開始 → 遅延なくスコアが付与される
- `asyncio.create_task()` でバックグラウンド実行 → 生成パイプラインをブロックしない
- 別ワーカープロセスを新設するとデプロイ複雑度が増すため、同一プロセス内で処理

### 5.2 新規モジュール: `quality_analyzer.py`

```python
# worker/quality_analyzer.py

import asyncio
import json
import re
import subprocess
from dataclasses import dataclass
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from .models import Track, TrackQualityScore

ANALYSIS_VERSION = 1

@dataclass
class AudioFeatures:
    # ffprobe
    duration_sec: float
    bitrate_kbps: int
    sample_rate: int
    channels: int
    file_size_bytes: int
    codec_name: str
    # silencedetect
    silence_duration_sec: float
    silence_ratio: float
    silence_count: int
    # volumedetect
    mean_volume_db: float
    max_volume_db: float
    # astats
    rms_level_db: float
    crest_factor_db: float
    flat_factor: float

async def analyze_track_quality(session: AsyncSession, track: Track) -> None:
    """トラック生成後フックから非同期で呼び出す"""
    try:
        features = await asyncio.get_event_loop().run_in_executor(
            None, _extract_features_sync, track.file_path
        )
        scores = _compute_scores(features)
        await _save_quality_score(session, track.id, features, scores)
    except Exception as e:
        await _save_error(session, track.id, str(e))

def _extract_features_sync(file_path: str) -> AudioFeatures:
    """ffprobe + ffmpeg フィルターで特徴量を同期抽出"""
    probe = _run_ffprobe(file_path)
    silence = _run_silencedetect(file_path)
    volume = _run_volumedetect(file_path)
    stats = _run_astats(file_path)
    return AudioFeatures(...)  # 各値をパース・組み立て

def _compute_scores(f: AudioFeatures) -> dict:
    """スコアリングロジック（§3参照）"""
    duration_score = _score_duration(f.duration_sec)
    silence_score  = _score_silence(f.silence_ratio)
    volume_score   = _score_volume(f.mean_volume_db)
    bitrate_score  = _score_bitrate(f.bitrate_kbps)
    dynamic_score  = _score_dynamic(f.crest_factor_db)
    overall = (
        duration_score * 0.20 +
        silence_score  * 0.25 +
        volume_score   * 0.20 +
        bitrate_score  * 0.15 +
        dynamic_score  * 0.20
    )
    grade = "A" if overall >= 80 else "B" if overall >= 60 else "C" if overall >= 40 else "D"
    return {
        "duration_score": duration_score,
        "silence_score": silence_score,
        "volume_score": volume_score,
        "bitrate_score": bitrate_score,
        "dynamic_score": dynamic_score,
        "overall_score": overall,
        "grade": grade,
    }
```

### 5.3 `queue_consumer.py` への変更箇所

```python
# process_request() 末尾に追加（既存コードの変更は最小限）
async def process_request(self, session, request):
    # ... 既存の生成・保存処理 ...
    track = Track(...)
    session.add(track)
    await session.commit()

    # 品質分析をバックグラウンドで起動（生成パイプラインをブロックしない）
    asyncio.create_task(
        analyze_track_quality(session_factory(), track)
    )
    return track
```

### 5.4 入力値サニタイズ方針（セキュリティ設計）

- `file_path` は DB から取得した内部パスのみ使用。ユーザー入力を一切受け取らない
- `subprocess.run()` に `shell=False` を強制。コマンドインジェクション不可
- ffprobe/ffmpeg の出力は正規表現でパース。eval/exec 不使用
- 数値パース時は `float()` / `int()` で型強制。不正値は `ValueError` でキャッチしエラー記録

---

## 6. API設計

### 6.1 `GET /api/tracks/{track_id}/quality`

#### レスポンス（200 OK）
```json
{
  "track_id": "uuid",
  "overall_score": 82.5,
  "grade": "A",
  "analyzed_at": "2026-03-24T10:00:00Z",
  "scores": {
    "duration": 100.0,
    "silence": 90.0,
    "volume": 75.0,
    "bitrate": 80.0,
    "dynamic": 65.0
  },
  "features": {
    "duration_sec": 185.3,
    "bitrate_kbps": 1024,
    "sample_rate": 44100,
    "channels": 2,
    "silence_ratio": 0.03,
    "mean_volume_db": -15.2,
    "max_volume_db": -3.1,
    "crest_factor_db": 12.4
  }
}
```

#### エラーケース
| ケース | ステータス |
|--------|----------|
| track_id が存在しない | 404 |
| 分析未完了（生成直後） | 404 + `{"detail": "Quality analysis not yet available"}` |
| 分析失敗（error_message あり） | 200 + `{"error": "Analysis failed: ..."}` |

### 6.2 `GET /api/quality/stats`

#### クエリパラメータ
| パラメータ | 型 | デフォルト | 説明 |
|-----------|---|----------|------|
| `channel_slug` | string | null | チャンネル絞り込み |
| `since` | ISO8601 | 7日前 | 集計開始日時 |

#### レスポンス（200 OK）
```json
{
  "summary": {
    "total_analyzed": 342,
    "avg_overall_score": 71.4,
    "grade_distribution": {
      "A": 98,
      "B": 145,
      "C": 72,
      "D": 27
    }
  },
  "by_channel": [
    {
      "channel_slug": "lo-fi",
      "avg_score": 78.2,
      "track_count": 85,
      "low_quality_count": 5
    }
  ],
  "low_quality_tracks": [
    {
      "track_id": "uuid",
      "channel_slug": "lo-fi",
      "overall_score": 28.0,
      "grade": "D",
      "silence_ratio": 0.52
    }
  ],
  "score_percentiles": {
    "p25": 61.0,
    "p50": 72.5,
    "p75": 83.0,
    "p90": 91.0
  }
}
```

---

## 7. 非機能要件

### パフォーマンス
- ffprobe + ffmpeg 3コマンド実行時間: 2〜8秒/トラック（180秒FLACの場合）
- `run_in_executor()` でイベントループをブロックしない
- 同時分析数: ワーカーあたり最大2タスク（CPU使用率監視のため）

### スケーラビリティ
- `analysis_version` フィールドにより、スコアリングロジック変更時の一括再分析が可能
- 再分析: `UPDATE track_quality_scores SET ... WHERE analysis_version < CURRENT_VERSION`

### テスタビリティ（AC記述）
- `_extract_features_sync()` は純粋関数（ファイルパスを引数に取る）→ テスト用FLACで単体テスト可能
- `_compute_scores()` は `AudioFeatures` を引数とする純粋関数 → モック不要でユニットテスト可能
- `analyze_track_quality()` はDBセッションをDI → モックセッションで統合テスト可能
- 並行性テストケース: 同一 `track_id` に対して複数ワーカーが同時分析開始した場合の重複防止（`ON CONFLICT DO NOTHING` または `INSERT ... ON CONFLICT (track_id) DO UPDATE`）

### 並行性制御
- `track_quality_scores.track_id` に `UNIQUE` 制約あり
- 複数ワーカー同時起動時の競合: `INSERT ... ON CONFLICT (track_id) DO UPDATE SET ... WHERE track_quality_scores.analysis_version < EXCLUDED.analysis_version` で安全にupsert

---

## 8. Alembicマイグレーション

新規ファイル: `alembic/versions/006_track_quality_scores.py`

```python
def upgrade():
    op.create_table(
        "track_quality_scores",
        sa.Column("id", UUID(), primary_key=True),
        sa.Column("track_id", UUID(), sa.ForeignKey("tracks.id", ondelete="CASCADE"), nullable=False, unique=True),
        # ... 全カラム ...
        sa.Column("analysis_version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("analyzed_at", sa.TIMESTAMPTZ(), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("error_message", sa.Text()),
        sa.Column("created_at", sa.TIMESTAMPTZ(), nullable=False, server_default=sa.text("NOW()")),
    )
    op.create_index("idx_track_quality_track", "track_quality_scores", ["track_id"])
    op.create_index("idx_track_quality_overall", "track_quality_scores", [sa.text("overall_score DESC NULLS LAST")])
    op.create_index("idx_track_quality_analyzed", "track_quality_scores", ["analyzed_at"])
    op.create_index("idx_track_quality_grade", "track_quality_scores", ["grade"])

def downgrade():
    op.drop_table("track_quality_scores")
```

---

## 9. 設計サマリー

| 設計項目 | 決定事項 |
|--------|--------|
| 特徴量取得 | ffprobe + silencedetect + volumedetect + astats（3コマンド） |
| スコア算出 | 5指標の重み付き平均（silence 25%、duration/volume/dynamic 各20%、bitrate 15%） |
| DBテーブル | `track_quality_scores`（独立テーブル、tracks への影響なし） |
| ワーカー統合 | 生成後フック（`asyncio.create_task`、ノンブロッキング） |
| 並行性制御 | UNIQUE制約 + upsert（ON CONFLICT DO UPDATE） |
| セキュリティ | shell=False、ユーザー入力経路なし、正規表現パース |
| API | GET /api/tracks/{id}/quality + GET /api/quality/stats |
