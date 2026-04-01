"""プレイリスト API — プレイリスト管理・トラック操作"""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Header, HTTPException, Response
from sqlalchemy import delete, func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from api.db import get_session
from api.schemas import (
    AddTrackBody,
    AddTrackResult,
    AddTracksResponse,
    FavoritesResponse,
    FavoriteTrackInfo,
    PlaylistCreateBody,
    PlaylistDetailResponse,
    PlaylistListResponse,
    PlaylistResponse,
    PlaylistSummaryResponse,
    PlaylistTrackEntry,
    PlaylistTrackInfo,
    PlaylistUpdateBody,
    ReorderTracksBody,
    ReorderTracksResponse,
)
from worker.models import Playlist, PlaylistTrack, Reaction, Track

router = APIRouter(tags=["playlists"])

MAX_PLAYLISTS_PER_SESSION = 50
MAX_TRACKS_PER_PLAYLIST = 200


def _require_session(x_session_id: str | None = Header(default=None)) -> str:
    if not x_session_id:
        raise HTTPException(status_code=400, detail="X-Session-ID ヘッダーが必要です")
    return x_session_id


async def _get_playlist_or_404(
    session: AsyncSession, playlist_id: uuid.UUID
) -> Playlist:
    playlist = await session.get(Playlist, playlist_id)
    if not playlist:
        raise HTTPException(status_code=404, detail="プレイリストが見つかりません")
    return playlist


def _check_owner(playlist: Playlist, session_id: str) -> None:
    if playlist.session_id != session_id:
        raise HTTPException(status_code=403, detail="このプレイリストへのアクセス権がありません")


async def _track_count(session: AsyncSession, playlist_id: uuid.UUID) -> int:
    result = await session.execute(
        select(func.count())
        .select_from(PlaylistTrack)
        .where(PlaylistTrack.playlist_id == playlist_id)
    )
    return result.scalar() or 0


# --- POST /api/playlists ---

@router.post("/api/playlists", response_model=PlaylistResponse, status_code=201)
async def create_playlist(
    body: PlaylistCreateBody,
    session_id: str = Depends(_require_session),
    db: AsyncSession = Depends(get_session),
) -> PlaylistResponse:
    count_result = await db.execute(
        select(func.count())
        .select_from(Playlist)
        .where(Playlist.session_id == session_id)
    )
    if (count_result.scalar() or 0) >= MAX_PLAYLISTS_PER_SESSION:
        raise HTTPException(
            status_code=422,
            detail=f"プレイリスト上限（{MAX_PLAYLISTS_PER_SESSION}件）に達しています",
        )

    dup_result = await db.execute(
        select(func.count())
        .select_from(Playlist)
        .where(Playlist.session_id == session_id, Playlist.name == body.name)
    )
    if (dup_result.scalar() or 0) > 0:
        raise HTTPException(status_code=409, detail="同じ名前のプレイリストが既に存在します")

    playlist = Playlist(
        name=body.name,
        description=body.description,
        cover_image_url=body.cover_image_url,
        session_id=session_id,
    )
    db.add(playlist)
    await db.commit()
    await db.refresh(playlist)

    return PlaylistResponse(
        id=playlist.id,
        name=playlist.name,
        description=playlist.description,
        cover_image_url=playlist.cover_image_url,
        track_count=0,
        created_at=playlist.created_at,
        updated_at=playlist.updated_at,
    )


# --- GET /api/playlists ---

@router.get("/api/playlists", response_model=PlaylistListResponse)
async def list_playlists(
    limit: int = 50,
    offset: int = 0,
    session_id: str = Depends(_require_session),
    db: AsyncSession = Depends(get_session),
) -> PlaylistListResponse:
    if limit < 1 or limit > 50:
        raise HTTPException(status_code=400, detail="limit は 1〜50 の範囲で指定してください")

    total_result = await db.execute(
        select(func.count())
        .select_from(Playlist)
        .where(Playlist.session_id == session_id)
    )
    total = total_result.scalar() or 0

    rows = await db.execute(
        select(Playlist)
        .where(Playlist.session_id == session_id)
        .order_by(Playlist.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    playlists = rows.scalars().all()

    items = []
    for pl in playlists:
        cnt = await _track_count(db, pl.id)
        items.append(
            PlaylistSummaryResponse(
                id=pl.id,
                name=pl.name,
                description=pl.description,
                cover_image_url=pl.cover_image_url,
                track_count=cnt,
                created_at=pl.created_at,
                updated_at=pl.updated_at,
            )
        )

    return PlaylistListResponse(
        playlists=items,
        total=total,
        limit=limit,
        offset=offset,
    )


# --- GET /api/playlists/{playlist_id} ---

@router.get("/api/playlists/{playlist_id}", response_model=PlaylistDetailResponse)
async def get_playlist(
    playlist_id: uuid.UUID,
    session_id: str = Depends(_require_session),
    db: AsyncSession = Depends(get_session),
) -> PlaylistDetailResponse:
    result = await db.execute(
        select(Playlist)
        .where(Playlist.id == playlist_id)
        .options(selectinload(Playlist.playlist_tracks).selectinload(PlaylistTrack.track))
    )
    playlist = result.scalar_one_or_none()
    if not playlist:
        raise HTTPException(status_code=404, detail="プレイリストが見つかりません")
    _check_owner(playlist, session_id)

    tracks = [
        PlaylistTrackEntry(
            position=pt.position,
            added_at=pt.added_at,
            track=PlaylistTrackInfo(
                id=pt.track.id,
                title=pt.track.title,
                mood=pt.track.mood,
                caption=pt.track.caption,
                duration_ms=pt.track.duration_ms,
                bpm=pt.track.bpm,
                music_key=pt.track.music_key,
                play_count=pt.track.play_count,
                like_count=pt.track.like_count,
                quality_score=pt.track.quality_score,
                channel_id=pt.track.channel_id,
                created_at=pt.track.created_at,
            ),
        )
        for pt in sorted(playlist.playlist_tracks, key=lambda x: x.position)
    ]

    return PlaylistDetailResponse(
        id=playlist.id,
        name=playlist.name,
        description=playlist.description,
        cover_image_url=playlist.cover_image_url,
        track_count=len(tracks),
        created_at=playlist.created_at,
        updated_at=playlist.updated_at,
        tracks=tracks,
    )


# --- PATCH /api/playlists/{playlist_id} ---

@router.patch("/api/playlists/{playlist_id}", response_model=PlaylistResponse)
async def update_playlist(
    playlist_id: uuid.UUID,
    body: PlaylistUpdateBody,
    session_id: str = Depends(_require_session),
    db: AsyncSession = Depends(get_session),
) -> PlaylistResponse:
    playlist = await _get_playlist_or_404(db, playlist_id)
    _check_owner(playlist, session_id)

    values: dict = {"updated_at": func.now()}
    if body.name is not None:
        values["name"] = body.name
    if body.description is not None:
        values["description"] = body.description
    if body.cover_image_url is not None:
        values["cover_image_url"] = body.cover_image_url

    await db.execute(
        update(Playlist).where(Playlist.id == playlist_id).values(**values)
    )
    await db.commit()
    await db.refresh(playlist)

    cnt = await _track_count(db, playlist.id)
    return PlaylistResponse(
        id=playlist.id,
        name=playlist.name,
        description=playlist.description,
        cover_image_url=playlist.cover_image_url,
        track_count=cnt,
        created_at=playlist.created_at,
        updated_at=playlist.updated_at,
    )


# --- DELETE /api/playlists/{playlist_id} --- (DR-002: 204 No Content)

@router.delete("/api/playlists/{playlist_id}", status_code=204)
async def delete_playlist(
    playlist_id: uuid.UUID,
    session_id: str = Depends(_require_session),
    db: AsyncSession = Depends(get_session),
) -> Response:
    playlist = await _get_playlist_or_404(db, playlist_id)
    _check_owner(playlist, session_id)

    await db.execute(delete(Playlist).where(Playlist.id == playlist_id))
    await db.commit()

    return Response(status_code=204)


# --- POST /api/playlists/{playlist_id}/duplicate ---

@router.post(
    "/api/playlists/{playlist_id}/duplicate",
    response_model=PlaylistResponse,
    status_code=201,
)
async def duplicate_playlist(
    playlist_id: uuid.UUID,
    session_id: str = Depends(_require_session),
    db: AsyncSession = Depends(get_session),
) -> PlaylistResponse:
    result = await db.execute(
        select(Playlist)
        .where(Playlist.id == playlist_id)
        .options(selectinload(Playlist.playlist_tracks).selectinload(PlaylistTrack.track))
    )
    original = result.scalar_one_or_none()
    if not original:
        raise HTTPException(status_code=404, detail="プレイリストが見つかりません")
    _check_owner(original, session_id)

    count_result = await db.execute(
        select(func.count())
        .select_from(Playlist)
        .where(Playlist.session_id == session_id)
    )
    if (count_result.scalar() or 0) >= MAX_PLAYLISTS_PER_SESSION:
        raise HTTPException(
            status_code=422,
            detail=f"プレイリスト上限（{MAX_PLAYLISTS_PER_SESSION}件）に達しています",
        )

    new_playlist = Playlist(
        name=f"{original.name} のコピー",
        description=original.description,
        cover_image_url=original.cover_image_url,
        session_id=session_id,
    )
    db.add(new_playlist)
    await db.flush()

    for pt in sorted(original.playlist_tracks, key=lambda x: x.position):
        new_pt = PlaylistTrack(
            playlist_id=new_playlist.id,
            track_id=pt.track_id,
            position=pt.position,
        )
        db.add(new_pt)

    await db.commit()
    await db.refresh(new_playlist)

    cnt = await _track_count(db, new_playlist.id)
    return PlaylistResponse(
        id=new_playlist.id,
        name=new_playlist.name,
        description=new_playlist.description,
        cover_image_url=new_playlist.cover_image_url,
        track_count=cnt,
        created_at=new_playlist.created_at,
        updated_at=new_playlist.updated_at,
    )


# --- POST /api/playlists/{playlist_id}/tracks --- (DR-004: bulk add)

@router.post(
    "/api/playlists/{playlist_id}/tracks",
    response_model=AddTracksResponse,
    status_code=201,
)
async def add_tracks(
    playlist_id: uuid.UUID,
    body: AddTrackBody,
    session_id: str = Depends(_require_session),
    db: AsyncSession = Depends(get_session),
) -> AddTracksResponse:
    playlist = await _get_playlist_or_404(db, playlist_id)
    _check_owner(playlist, session_id)

    current_count = await _track_count(db, playlist_id)
    if current_count + len(body.track_ids) > MAX_TRACKS_PER_PLAYLIST:
        raise HTTPException(
            status_code=422,
            detail=f"追加するとトラック上限（{MAX_TRACKS_PER_PLAYLIST}件）を超えます",
        )

    added: list[AddTrackResult] = []
    position = current_count

    for track_id in body.track_ids:
        track = await db.get(Track, track_id)
        if not track or track.is_retired:
            raise HTTPException(
                status_code=404, detail=f"トラックが見つかりません: {track_id}"
            )

        pt = PlaylistTrack(
            playlist_id=playlist_id,
            track_id=track_id,
            position=position,
        )
        db.add(pt)
        try:
            await db.flush()
        except IntegrityError:
            await db.rollback()
            raise HTTPException(
                status_code=409,
                detail=f"このトラックはすでにプレイリストに追加されています: {track_id}",
            ) from None

        await db.refresh(pt)
        added.append(
            AddTrackResult(
                track_id=pt.track_id,
                position=pt.position,
                added_at=pt.added_at,
            )
        )
        position += 1

    await db.commit()

    return AddTracksResponse(playlist_id=playlist_id, added=added)


# --- DELETE /api/playlists/{playlist_id}/tracks/{track_id} --- (DR-002: 204 No Content)

@router.delete(
    "/api/playlists/{playlist_id}/tracks/{track_id}",
    status_code=204,
)
async def remove_track(
    playlist_id: uuid.UUID,
    track_id: uuid.UUID,
    session_id: str = Depends(_require_session),
    db: AsyncSession = Depends(get_session),
) -> Response:
    playlist = await _get_playlist_or_404(db, playlist_id)
    _check_owner(playlist, session_id)

    result = await db.execute(
        delete(PlaylistTrack).where(
            PlaylistTrack.playlist_id == playlist_id,
            PlaylistTrack.track_id == track_id,
        )
    )
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="トラックがプレイリストに存在しません")

    remaining = await db.execute(
        select(PlaylistTrack)
        .where(PlaylistTrack.playlist_id == playlist_id)
        .order_by(PlaylistTrack.position)
    )
    for i, pt in enumerate(remaining.scalars().all()):
        pt.position = i

    await db.commit()

    return Response(status_code=204)


# --- PUT /api/playlists/{playlist_id}/tracks/reorder ---

@router.put(
    "/api/playlists/{playlist_id}/tracks/reorder",
    response_model=ReorderTracksResponse,
)
async def reorder_tracks(
    playlist_id: uuid.UUID,
    body: ReorderTracksBody,
    session_id: str = Depends(_require_session),
    db: AsyncSession = Depends(get_session),
) -> ReorderTracksResponse:
    playlist = await _get_playlist_or_404(db, playlist_id)
    _check_owner(playlist, session_id)

    existing = await db.execute(
        select(PlaylistTrack).where(PlaylistTrack.playlist_id == playlist_id)
    )
    pts = {pt.track_id: pt for pt in existing.scalars().all()}

    if set(body.track_ids) != set(pts.keys()) or len(body.track_ids) != len(pts):
        raise HTTPException(
            status_code=400,
            detail="track_ids がプレイリストの現在のトラック一覧と一致しません",
        )

    for i, track_id in enumerate(body.track_ids):
        pts[track_id].position = i

    await db.commit()

    return ReorderTracksResponse(ok=True)


# --- GET /api/favorites ---

@router.get("/api/favorites", response_model=FavoritesResponse)
async def get_favorites(
    limit: int = 50,
    offset: int = 0,
    session_id: str = Depends(_require_session),
    db: AsyncSession = Depends(get_session),
) -> FavoritesResponse:
    total_result = await db.execute(
        select(func.count())
        .select_from(Reaction)
        .where(
            Reaction.session_id == session_id,
            Reaction.reaction_type == "like",
        )
    )
    total = total_result.scalar() or 0

    rows = await db.execute(
        select(Reaction, Track)
        .join(Track, Reaction.track_id == Track.id)
        .where(
            Reaction.session_id == session_id,
            Reaction.reaction_type == "like",
        )
        .order_by(Reaction.created_at.desc())
        .limit(limit)
        .offset(offset)
    )

    tracks = [
        FavoriteTrackInfo(
            id=track.id,
            title=track.title,
            mood=track.mood,
            duration_ms=track.duration_ms,
            bpm=track.bpm,
            like_count=track.like_count,
            quality_score=track.quality_score,
            channel_id=track.channel_id,
            liked_at=reaction.created_at,
        )
        for reaction, track in rows.all()
    ]

    return FavoritesResponse(
        tracks=tracks,
        total=total,
        limit=limit,
        offset=offset,
    )
