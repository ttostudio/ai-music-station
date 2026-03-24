"""共有リンク API — シェアトークン発行 / OGP ページ返却"""
from __future__ import annotations

import hashlib
import logging
import secrets

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.config import settings
from api.db import get_session
from api.schemas import ShareLinkResponse
from worker.models import Channel, ShareLink, Track, TrackAnalytics

logger = logging.getLogger(__name__)

router = APIRouter(tags=["shares"])

SHARE_PAGE_TEMPLATE = """\
<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title} | AI Music Station</title>
  <meta property="og:type" content="music.song">
  <meta property="og:title" content="{title}">
  <meta property="og:description" content="{description}">
  <meta property="og:url" content="{share_url}">
  <meta property="og:image" content="{og_image_url}">
  <meta property="og:image:width" content="1200">
  <meta property="og:image:height" content="630">
  <meta property="og:site_name" content="AI Music Station">
  <meta property="og:locale" content="ja_JP">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="{title}">
  <meta name="twitter:description" content="{description}">
  <meta name="twitter:image" content="{og_image_url}">
  <style>
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    body {{ font-family: -apple-system, BlinkMacSystemFont, sans-serif;
           background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
           color: #fff; min-height: 100vh; display: flex; align-items: center;
           justify-content: center; }}
    .card {{ background: rgba(255,255,255,0.08); backdrop-filter: blur(20px);
             border-radius: 16px; padding: 2rem; max-width: 480px; width: 90%;
             text-align: center; }}
    .card h1 {{ font-size: 1.5rem; margin-bottom: 0.5rem; }}
    .card p {{ color: rgba(255,255,255,0.7); margin-bottom: 1.5rem; }}
    audio {{ width: 100%; margin-bottom: 1rem; }}
    .link {{ color: #64b5f6; text-decoration: none; }}
    .link:hover {{ text-decoration: underline; }}
  </style>
</head>
<body>
  <div class="card">
    <h1>{title}</h1>
    <p>{description}</p>
    <audio controls preload="metadata" src="{audio_url}"></audio>
    <p><a class="link" href="{base_url}">AI Music Station で聴く</a></p>
  </div>
  <script>
    (function() {{
      var played = false;
      var audio = document.querySelector('audio');
      if (audio) {{
        audio.addEventListener('play', function() {{
          if (played) return;
          played = true;
          fetch('{base_url}/api/analytics/play', {{
            method: 'POST',
            headers: {{ 'Content-Type': 'application/json' }},
            body: JSON.stringify({{ track_id: '{track_id}', share_token: '{share_token}' }})
          }}).catch(function() {{}});
        }});
      }}
    }})();
  </script>
</body>
</html>
"""


def _hash_ip(ip: str) -> str:
    return hashlib.sha256(
        (ip + settings.analytics_ip_salt).encode()
    ).hexdigest()


@router.post(
    "/api/tracks/{track_id}/share",
    response_model=ShareLinkResponse,
)
async def create_share_link(
    track_id: str,
    session: AsyncSession = Depends(get_session),
) -> ShareLinkResponse:
    """シェアトークンを発行する（idempotent: 既存があれば再利用）"""
    track = await session.get(Track, track_id)
    if not track or track.is_retired:
        raise HTTPException(status_code=404, detail="Track not found")

    # 既存トークン検索
    result = await session.execute(
        select(ShareLink)
        .where(ShareLink.track_id == track.id)
        .order_by(ShareLink.created_at.desc())
        .limit(1)
    )
    existing = result.scalar_one_or_none()
    if existing:
        return ShareLinkResponse(
            share_token=existing.share_token,
            share_url=f"{settings.public_base_url}/share/{existing.share_token}",
            track_id=track.id,
        )

    # 新規トークン生成（衝突時リトライ最大3回）
    for _ in range(3):
        token = secrets.token_urlsafe(32)
        link = ShareLink(track_id=track.id, share_token=token)
        session.add(link)
        try:
            await session.flush()
            break
        except Exception:
            await session.rollback()
    else:
        raise HTTPException(
            status_code=500, detail="Failed to generate share token"
        )

    await session.commit()
    return ShareLinkResponse(
        share_token=token,
        share_url=f"{settings.public_base_url}/share/{token}",
        track_id=track.id,
    )


@router.get("/share/{token}", response_class=HTMLResponse)
async def share_page(
    token: str,
    request: Request,
    session: AsyncSession = Depends(get_session),
) -> HTMLResponse:
    """OGP メタタグ付き共有ページを返す"""
    # トークンバリデーション（英数字+ハイフン+アンダースコアのみ、最大64文字）
    if not token or len(token) > 64:
        raise HTTPException(status_code=404, detail="Not found")

    result = await session.execute(
        select(ShareLink).where(ShareLink.share_token == token)
    )
    link = result.scalar_one_or_none()
    if not link:
        raise HTTPException(status_code=404, detail="Not found")

    track = await session.get(Track, link.track_id)
    if not track or track.is_retired:
        raise HTTPException(status_code=404, detail="Not found")

    # チャンネル情報取得
    channel = await session.get(Channel, track.channel_id)
    channel_name = channel.name if channel else "AI Music Station"

    # share_view イベント記録（fire-and-forget）
    try:
        ip = request.client.host if request.client else ""
        analytics = TrackAnalytics(
            track_id=track.id,
            event_type="share_view",
            ip_hash=_hash_ip(ip) if ip else None,
            user_agent=(request.headers.get("user-agent") or "")[:500] or None,
            referer=(request.headers.get("referer") or "")[:500] or None,
            share_token=token,
        )
        session.add(analytics)
        await session.commit()
    except Exception:
        logger.warning("Failed to record share_view event", exc_info=True)

    title = track.title or track.caption or "Untitled"
    description = track.caption or ""
    if track.mood:
        description = f"{description} #{track.mood}"
    description = f"{description} #{channel_name}".strip()

    base_url = settings.public_base_url.rstrip("/")
    share_url = f"{base_url}/share/{token}"
    audio_url = f"{base_url}/api/tracks/{track.id}/audio"
    og_image_url = f"{base_url}/api/tracks/{track.id}/ogp-image"

    html = SHARE_PAGE_TEMPLATE.format(
        title=_escape_html(title),
        description=_escape_html(description),
        share_url=share_url,
        og_image_url=og_image_url,
        audio_url=audio_url,
        base_url=base_url,
        track_id=str(track.id),
        share_token=token,
    )
    return HTMLResponse(content=html, status_code=200)


def _escape_html(s: str) -> str:
    """OGP メタタグ用のHTML属性エスケープ"""
    return (
        s.replace("&", "&amp;")
        .replace('"', "&quot;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )
