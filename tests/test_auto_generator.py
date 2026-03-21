"""worker/auto_generator.py のテスト"""
from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from worker.auto_generator import (
    check_system_resources,
    create_auto_request,
    get_active_stock,
    get_pending_request_count,
    run_auto_generation,
)
from worker.lyrics_generator import LyricsResult
from worker.preference_analyzer import PreferenceProfile

# --- check_system_resources ---

@patch("worker.auto_generator.psutil")
def test_resources_available(mock_psutil):
    mock_psutil.cpu_percent.return_value = 50.0
    mock_psutil.virtual_memory.return_value = MagicMock(percent=60.0)
    assert check_system_resources() is True


@patch("worker.auto_generator.psutil")
def test_cpu_too_high(mock_psutil):
    mock_psutil.cpu_percent.return_value = 85.0
    mock_psutil.virtual_memory.return_value = MagicMock(percent=60.0)
    assert check_system_resources() is False


@patch("worker.auto_generator.psutil")
def test_memory_too_high(mock_psutil):
    mock_psutil.cpu_percent.return_value = 50.0
    mock_psutil.virtual_memory.return_value = MagicMock(percent=90.0)
    assert check_system_resources() is False


# --- get_active_stock ---

@pytest.mark.asyncio
async def test_get_active_stock():
    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar.return_value = 7
    mock_session.execute.return_value = mock_result

    count = await get_active_stock(mock_session, uuid.uuid4())
    assert count == 7


# --- get_pending_request_count ---

@pytest.mark.asyncio
async def test_get_pending_request_count():
    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar.return_value = 2
    mock_session.execute.return_value = mock_result

    count = await get_pending_request_count(mock_session, uuid.uuid4())
    assert count == 2


# --- create_auto_request ---

@pytest.mark.asyncio
@patch("worker.auto_generator.LyricsGenerator")
@patch("worker.auto_generator.analyze_channel_preferences")
async def test_create_auto_request_with_mood(mock_analyze, mock_gen_cls):
    mock_analyze.return_value = PreferenceProfile(
        channel_id=uuid.uuid4(),
        top_keywords=["jazz"],
        bpm_range=(90, 120),
        instrumental_ratio=0.8,
        sample_size=10,
        prompt_hint="listener-preferred elements: jazz",
    )
    mock_gen = MagicMock()
    mock_gen.generate.return_value = LyricsResult(
        title="テスト曲", caption="jazz piano", lyrics="[Verse]\ntest",
    )
    mock_gen_cls.return_value = mock_gen

    channel = MagicMock()
    channel.id = uuid.uuid4()
    channel.name = "Jazz Channel"
    channel.slug = "jazz"
    channel.description = "ジャズチャンネル"
    channel.mood_description = "夜のジャズカフェ"
    channel.default_instrumental = False

    session = AsyncMock()
    request = await create_auto_request(session, channel)

    assert request.mood == "夜のジャズカフェ (listener-preferred elements: jazz)"
    assert request.caption == "jazz piano"
    assert request.status == "pending"
    session.add.assert_called_once()
    session.commit.assert_awaited_once()


# --- run_auto_generation ---

@pytest.mark.asyncio
@patch("worker.auto_generator.check_system_resources", return_value=False)
async def test_skips_when_resources_unavailable(mock_check):
    factory = MagicMock()
    result = await run_auto_generation(factory)
    assert result == 0


@pytest.mark.asyncio
@patch("worker.auto_generator.create_auto_request", new_callable=AsyncMock)
@patch("worker.auto_generator.get_active_stock", new_callable=AsyncMock)
@patch(
    "worker.auto_generator.get_pending_request_count",
    new_callable=AsyncMock,
)
@patch("worker.auto_generator.check_system_resources", return_value=True)
async def test_creates_requests_for_low_stock(
    mock_check, mock_pending, mock_stock, mock_create,
):
    channel = MagicMock()
    channel.id = uuid.uuid4()
    channel.slug = "lofi"
    channel.min_stock = 5
    channel.auto_generate = True
    channel.is_active = True

    mock_pending.return_value = 0
    mock_stock.return_value = 2
    mock_create.return_value = MagicMock()

    mock_session = AsyncMock()
    mock_scalars = MagicMock()
    mock_scalars.all.return_value = [channel]
    mock_result = MagicMock()
    mock_result.scalars.return_value = mock_scalars
    mock_session.execute.return_value = mock_result

    factory = MagicMock()
    factory.return_value.__aenter__ = AsyncMock(return_value=mock_session)
    factory.return_value.__aexit__ = AsyncMock(return_value=False)

    result = await run_auto_generation(factory)
    assert result == 1
    mock_create.assert_awaited_once()


@pytest.mark.asyncio
@patch("worker.auto_generator.create_auto_request", new_callable=AsyncMock)
@patch("worker.auto_generator.get_active_stock", new_callable=AsyncMock)
@patch(
    "worker.auto_generator.get_pending_request_count",
    new_callable=AsyncMock,
)
@patch("worker.auto_generator.check_system_resources", return_value=True)
async def test_skips_when_stock_sufficient(
    mock_check, mock_pending, mock_stock, mock_create,
):
    channel = MagicMock()
    channel.id = uuid.uuid4()
    channel.slug = "lofi"
    channel.min_stock = 5

    mock_pending.return_value = 0
    mock_stock.return_value = 10

    mock_session = AsyncMock()
    mock_scalars = MagicMock()
    mock_scalars.all.return_value = [channel]
    mock_result = MagicMock()
    mock_result.scalars.return_value = mock_scalars
    mock_session.execute.return_value = mock_result

    factory = MagicMock()
    factory.return_value.__aenter__ = AsyncMock(return_value=mock_session)
    factory.return_value.__aexit__ = AsyncMock(return_value=False)

    result = await run_auto_generation(factory)
    assert result == 0
    mock_create.assert_not_awaited()


@pytest.mark.asyncio
@patch("worker.auto_generator.create_auto_request", new_callable=AsyncMock)
@patch("worker.auto_generator.get_active_stock", new_callable=AsyncMock)
@patch(
    "worker.auto_generator.get_pending_request_count",
    new_callable=AsyncMock,
)
@patch("worker.auto_generator.check_system_resources", return_value=True)
async def test_skips_when_pending_exists(
    mock_check, mock_pending, mock_stock, mock_create,
):
    channel = MagicMock()
    channel.id = uuid.uuid4()
    channel.slug = "lofi"
    channel.min_stock = 5

    mock_pending.return_value = 1

    mock_session = AsyncMock()
    mock_scalars = MagicMock()
    mock_scalars.all.return_value = [channel]
    mock_result = MagicMock()
    mock_result.scalars.return_value = mock_scalars
    mock_session.execute.return_value = mock_result

    factory = MagicMock()
    factory.return_value.__aenter__ = AsyncMock(return_value=mock_session)
    factory.return_value.__aexit__ = AsyncMock(return_value=False)

    result = await run_auto_generation(factory)
    assert result == 0
    mock_create.assert_not_awaited()
