# DB設計書 — プレイリスト機能

## 概要

プレイリスト機能のデータモデル定義。既存の `tracks` テーブルへの参照を持つ2テーブル構成。

---

## ER図（テキスト）

```
channels
  └── tracks (channel_id FK)
         ↑
         └── playlist_tracks (track_id FK)
                   │
                   └── playlists (playlist_id FK)
```

```
playlists
  id (PK, UUID)
  name
  description
  user_id (optional, session-based identifier)
  is_public
  created_at
  updated_at
    │
    └─ playlist_tracks
         id (PK, UUID)
         playlist_id (FK → playlists.id)
         track_id    (FK → tracks.id)
         position
         added_at
```

---

## テーブル定義

### playlists

| カラム名     | 型                          | 制約                              | 説明                                     |
|-----------|-----------------------------|-----------------------------------|------------------------------------------|
| id        | UUID                        | PK, default=uuid4                 | プレイリストID                             |
| name      | VARCHAR(100)                | NOT NULL                          | プレイリスト名                             |
| description | TEXT                      | NULL許可                          | 説明文                                   |
| user_id   | VARCHAR(100)                | NULL許可                          | 作成者のセッションID（認証なし。任意）       |
| is_public | BOOLEAN                     | NOT NULL, default=true            | 公開/非公開フラグ                          |
| created_at | TIMESTAMP WITH TIME ZONE   | NOT NULL, server_default=now()    | 作成日時                                  |
| updated_at | TIMESTAMP WITH TIME ZONE   | NOT NULL, server_default=now()    | 更新日時                                  |

**インデックス:**

| インデックス名                    | 対象カラム                | 種別    | 用途                         |
|----------------------------------|--------------------------|---------|------------------------------|
| `idx_playlists_user_created`     | (user_id, created_at)    | BTREE   | ユーザー別プレイリスト一覧取得 |
| `idx_playlists_public_created`   | (is_public, created_at)  | BTREE   | 公開プレイリスト一覧取得       |

---

### playlist_tracks

| カラム名       | 型                        | 制約                                             | 説明                             |
|--------------|---------------------------|--------------------------------------------------|----------------------------------|
| id           | UUID                      | PK, default=uuid4                                | レコードID                        |
| playlist_id  | UUID                      | NOT NULL, FK → playlists.id ON DELETE CASCADE    | プレイリストID                    |
| track_id     | UUID                      | NOT NULL, FK → tracks.id ON DELETE CASCADE       | トラックID                        |
| position     | INTEGER                   | NOT NULL, CHECK(position >= 0)                   | 表示順（0始まり）                  |
| added_at     | TIMESTAMP WITH TIME ZONE  | NOT NULL, server_default=now()                   | 追加日時                          |

**制約:**

| 制約名                                  | 対象カラム                    | 種別   | 説明                                   |
|----------------------------------------|------------------------------|--------|----------------------------------------|
| `uq_playlist_tracks_playlist_track`    | (playlist_id, track_id)      | UNIQUE | 同一プレイリストへの重複トラック追加防止  |

**インデックス:**

| インデックス名                         | 対象カラム              | 種別    | 用途                              |
|--------------------------------------|------------------------|---------|-----------------------------------|
| `idx_playlist_tracks_playlist_pos`   | (playlist_id, position) | BTREE   | プレイリスト内トラック一覧取得（順序付き） |
| `idx_playlist_tracks_track`          | (track_id)              | BTREE   | トラック削除時のカスケード処理           |

---

## SQLAlchemy モデル定義（参考実装）

```python
# worker/models.py に追記

class Playlist(Base):
    __tablename__ = "playlists"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    user_id: Mapped[Optional[str]] = mapped_column(String(100))
    is_public: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default="true"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    playlist_tracks: Mapped[List["PlaylistTrack"]] = relationship(
        back_populates="playlist",
        order_by="PlaylistTrack.position",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("idx_playlists_user_created", "user_id", "created_at"),
        Index("idx_playlists_public_created", "is_public", "created_at"),
    )


class PlaylistTrack(Base):
    __tablename__ = "playlist_tracks"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    playlist_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("playlists.id", ondelete="CASCADE"),
        nullable=False,
    )
    track_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tracks.id", ondelete="CASCADE"),
        nullable=False,
    )
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    added_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    playlist: Mapped["Playlist"] = relationship(back_populates="playlist_tracks")
    track: Mapped["Track"] = relationship()

    __table_args__ = (
        UniqueConstraint("playlist_id", "track_id", name="uq_playlist_tracks_playlist_track"),
        Index("idx_playlist_tracks_playlist_pos", "playlist_id", "position"),
        Index("idx_playlist_tracks_track", "track_id"),
    )
```

---

## Alembic マイグレーション

ファイル名: `alembic/versions/009_add_playlists.py`

```python
"""add playlists and playlist_tracks tables

Revision ID: 009
Revises: 008
Create Date: 2026-03-27
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "009"
down_revision = "008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "playlists",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("description", sa.Text),
        sa.Column("user_id", sa.String(100)),
        sa.Column("is_public", sa.Boolean, nullable=False, server_default="true"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("idx_playlists_user_created", "playlists", ["user_id", "created_at"])
    op.create_index("idx_playlists_public_created", "playlists", ["is_public", "created_at"])

    op.create_table(
        "playlist_tracks",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "playlist_id",
            UUID(as_uuid=True),
            sa.ForeignKey("playlists.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "track_id",
            UUID(as_uuid=True),
            sa.ForeignKey("tracks.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("position", sa.Integer, nullable=False),
        sa.Column(
            "added_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint("position >= 0", name="ck_playlist_tracks_position"),
        sa.UniqueConstraint("playlist_id", "track_id", name="uq_playlist_tracks_playlist_track"),
    )
    op.create_index("idx_playlist_tracks_playlist_pos", "playlist_tracks", ["playlist_id", "position"])
    op.create_index("idx_playlist_tracks_track", "playlist_tracks", ["track_id"])


def downgrade() -> None:
    op.drop_table("playlist_tracks")
    op.drop_table("playlists")
```

---

## 設計判断・考慮事項

### user_id について
- 現状のシステムに認証機構がないため、`user_id` はクライアントが管理するセッション識別子（例: ブラウザのローカルストレージに保存したUUID）
- NULL許可: 匿名プレイリストを許容
- 将来的に認証機能追加時に外部キー制約を後付け追加可能な設計

### 並べ替え戦略（position）
- position は 0始まりの整数。UNIQUE制約を設けず、並べ替えはアプリケーションレイヤーで全レコード一括更新
- 理由: 途中挿入・削除時のgap管理の複雑さを避けるため。トラック数が数百程度であれば一括更新のコストは許容範囲内
- `PUT /api/playlists/{id}/tracks/reorder` では全 position を渡し、一括 UPDATE する（後述のAPI設計参照）

### カスケード削除
- `playlists` 削除 → `playlist_tracks` は CASCADE DELETE
- `tracks` 削除（retired） → `playlist_tracks` は CASCADE DELETE（is_retired フラグによる論理削除ではなく、プレイリスト参照は物理削除）

### 並行性制御
- トラック追加（`POST /api/playlists/{id}/tracks`）は UNIQUE制約 `uq_playlist_tracks_playlist_track` によりデータベースレベルで重複を防ぐ
- 並べ替え（`PUT /api/playlists/{id}/tracks/reorder`）はトランザクション内で全件更新し、整合性を担保
- 同一プレイリストへの並行 reorder リクエストは最後のコミットが優先（Last-Write-Wins）。楽観的ロックは今回スコープ外

### パフォーマンス
- `GET /api/playlists/{id}` はプレイリスト取得と JOIN（または SELECT IN）でトラック情報を一度に取得
- トラック件数が多いケース（100件超）を考慮し、position インデックスを設定
