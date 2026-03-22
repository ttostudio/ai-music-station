"""worker/auto_generator.py のテスト"""
from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from worker.auto_generator import (
    check_system_resources,
    create_auto_request,
    get_active_stock,
    get_existing_titles,
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
@patch("worker.auto_generator.get_existing_titles", new_callable=AsyncMock)
@patch("worker.auto_generator.LyricsGenerator")
@patch("worker.auto_generator.analyze_channel_preferences")
async def test_create_auto_request_with_mood(mock_analyze, mock_gen_cls, mock_titles):
    mock_analyze.return_value = PreferenceProfile(
        channel_id=uuid.uuid4(),
        top_keywords=["jazz"],
        bpm_range=(90, 120),
        instrumental_ratio=0.8,
        sample_size=10,
        prompt_hint="listener-preferred elements: jazz",
    )
    mock_titles.return_value = ["夜風のささやき", "月明かりのワルツ"]
    mock_gen = MagicMock()
    mock_gen.generate = AsyncMock(return_value=LyricsResult(
        title="テスト曲", caption="jazz piano", lyrics="[Verse]\ntest",
    ))
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
    assert request.caption == "テスト曲 | jazz piano"
    assert request.status == "pending"
    session.add.assert_called_once()
    session.commit.assert_awaited_once()


@pytest.mark.asyncio
@patch("worker.auto_generator.get_existing_titles", new_callable=AsyncMock)
@patch("worker.auto_generator.LyricsGenerator")
@patch("worker.auto_generator.analyze_channel_preferences")
async def test_existing_titles_passed_to_generator(mock_analyze, mock_gen_cls, mock_titles):
    """既存タイトルがLyricsGeneratorに渡されることを確認"""
    mock_analyze.return_value = PreferenceProfile(
        channel_id=uuid.uuid4(),
        top_keywords=[],
        bpm_range=(90, 120),
        instrumental_ratio=0.5,
        sample_size=0,
        prompt_hint=None,
    )
    existing = ["夜風のささやき", "月明かりのワルツ", "星降る夜に"]
    mock_titles.return_value = existing
    mock_gen = MagicMock()
    mock_gen.generate = AsyncMock(return_value=LyricsResult(
        title="新しい曲", caption="test", lyrics="[Verse]\ntest",
    ))
    mock_gen_cls.return_value = mock_gen

    channel = MagicMock()
    channel.id = uuid.uuid4()
    channel.name = "Jazz"
    channel.slug = "jazz"
    channel.description = "ジャズ"
    channel.mood_description = "ジャズ"
    channel.default_instrumental = True

    session = AsyncMock()
    await create_auto_request(session, channel)

    # generate() に existing_titles が渡されたことを確認
    mock_gen.generate.assert_awaited_once()
    call_kwargs = mock_gen.generate.call_args
    assert call_kwargs.kwargs.get("existing_titles") == existing


# --- run_auto_generation ---

@pytest.mark.asyncio
@patch("worker.auto_generator.check_system_resources", return_value=False)
async def test_skips_when_resources_unavailable(mock_check):
    factory = MagicMock()
    result = await run_auto_generation(factory)
    assert result == 0


# --- get_existing_titles ---

@pytest.mark.asyncio
async def test_get_existing_titles():
    """既存タイトル一覧を取得できることを確認"""
    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_result.all.return_value = [("夜風のささやき",), ("月明かりのワルツ",)]
    mock_session.execute.return_value = mock_result

    titles = await get_existing_titles(mock_session, uuid.uuid4())
    assert titles == ["夜風のささやき", "月明かりのワルツ"]


# --- run_auto_generation ---

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


# --- 在庫不足チャンネル優先テスト ---

@pytest.mark.asyncio
@patch("worker.auto_generator.create_auto_request", new_callable=AsyncMock)
@patch("worker.auto_generator.get_active_stock", new_callable=AsyncMock)
@patch(
    "worker.auto_generator.get_pending_request_count",
    new_callable=AsyncMock,
)
@patch("worker.auto_generator.check_system_resources", return_value=True)
async def test_prioritizes_channel_with_largest_deficit(
    mock_check, mock_pending, mock_stock, mock_create,
):
    """在庫不足が最も大きいチャンネルが優先されることを確認"""
    # Jazz: stock=8, min_stock=10 → deficit=2
    jazz = MagicMock()
    jazz.id = uuid.uuid4()
    jazz.slug = "jazz"
    jazz.min_stock = 10
    jazz.max_stock = 50
    jazz.auto_generate = True
    jazz.is_active = True

    # Anime: stock=1, min_stock=5 → deficit=4（最大不足）
    anime = MagicMock()
    anime.id = uuid.uuid4()
    anime.slug = "anime"
    anime.min_stock = 5
    anime.max_stock = 50
    anime.auto_generate = True
    anime.is_active = True

    mock_pending.return_value = 0
    # get_active_stock はチャンネルIDごとに異なる値を返す
    stock_map = {jazz.id: 8, anime.id: 1}
    mock_stock.side_effect = lambda session, cid: stock_map[cid]
    mock_create.return_value = MagicMock()

    mock_session = AsyncMock()
    mock_scalars = MagicMock()
    mock_scalars.all.return_value = [jazz, anime]
    mock_result = MagicMock()
    mock_result.scalars.return_value = mock_scalars
    mock_session.execute.return_value = mock_result

    factory = MagicMock()
    factory.return_value.__aenter__ = AsyncMock(return_value=mock_session)
    factory.return_value.__aexit__ = AsyncMock(return_value=False)

    result = await run_auto_generation(factory)

    # 1曲のみ生成され、不足が大きいanimeチャンネルが優先される
    assert result == 1
    mock_create.assert_awaited_once()
    created_channel = mock_create.call_args[0][1]
    assert created_channel.slug == "anime"


@pytest.mark.asyncio
@patch("worker.auto_generator.create_auto_request", new_callable=AsyncMock)
@patch("worker.auto_generator.get_active_stock", new_callable=AsyncMock)
@patch(
    "worker.auto_generator.get_pending_request_count",
    new_callable=AsyncMock,
)
@patch("worker.auto_generator.check_system_resources", return_value=True)
async def test_generates_only_one_per_cycle(
    mock_check, mock_pending, mock_stock, mock_create,
):
    """1サイクルで最大1曲のみ生成されることを確認"""
    channels = []
    for slug in ["jazz", "anime", "game"]:
        ch = MagicMock()
        ch.id = uuid.uuid4()
        ch.slug = slug
        ch.min_stock = 5
        ch.max_stock = 50
        ch.auto_generate = True
        ch.is_active = True
        channels.append(ch)

    mock_pending.return_value = 0
    mock_stock.return_value = 0  # 全チャンネル在庫ゼロ
    mock_create.return_value = MagicMock()

    mock_session = AsyncMock()
    mock_scalars = MagicMock()
    mock_scalars.all.return_value = channels
    mock_result = MagicMock()
    mock_result.scalars.return_value = mock_scalars
    mock_session.execute.return_value = mock_result

    factory = MagicMock()
    factory.return_value.__aenter__ = AsyncMock(return_value=mock_session)
    factory.return_value.__aexit__ = AsyncMock(return_value=False)

    result = await run_auto_generation(factory)

    # 3チャンネルとも在庫不足だが、1曲のみ生成
    assert result == 1
    assert mock_create.await_count == 1
