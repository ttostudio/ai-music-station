from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import TYPE_CHECKING

from api.config import settings

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

_engine = None
_async_session = None


def _get_engine():
    global _engine
    if _engine is None:
        from sqlalchemy.ext.asyncio import create_async_engine

        _engine = create_async_engine(settings.database_url, echo=False)
    return _engine


def _get_session_factory():
    global _async_session
    if _async_session is None:
        from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

        _async_session = async_sessionmaker(
            _get_engine(), class_=AsyncSession, expire_on_commit=False
        )
    return _async_session


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    factory = _get_session_factory()
    async with factory() as session:
        yield session
