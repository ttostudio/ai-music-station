import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from worker.acestep_client import GenerationError, GenerationResult
from worker.models import Request
from worker.queue_consumer import QueueConsumer


@pytest.fixture
def mock_session_factory():
    return AsyncMock()


@pytest.fixture
def mock_client():
    from api.services.acestep_client import AceStepJobResult
    from pathlib import Path

    client = AsyncMock()

    async def _mock_generate_sync(params: dict, dest_path: Path) -> AceStepJobResult:
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        dest_path.write_bytes(b"fake-mp3-data")
        return AceStepJobResult(
            status="completed",
            audio_path=str(dest_path),
            duration=180.0,
            bpm=80,
            key_scale="Am",
        )

    client.generate_sync = _mock_generate_sync
    return client


@pytest.fixture
def consumer(mock_session_factory, mock_client, tmp_path):
    return QueueConsumer(
        session_factory=mock_session_factory,
        client=mock_client,
        tracks_dir=str(tmp_path / "tracks"),
        worker_id="test-worker",
    )


class TestBuildGenerationParams:
    def test_uses_channel_preset_when_no_user_input(self, consumer, sample_channel, sample_request):
        params = consumer.build_generation_params(sample_request, sample_channel)
        assert "lo-fi" in params.caption.lower() or "lo-fi" in params.caption
        assert params.instrumental is True
        assert 70 <= params.bpm <= 90
        assert params.duration == 180

    def test_user_caption_combined_with_preset(self, consumer, sample_channel, sample_request):
        sample_request.caption = "rainy day vibes"
        params = consumer.build_generation_params(sample_request, sample_channel)
        assert "rainy day vibes" in params.caption
        assert "lo-fi" in params.caption.lower()

    def test_user_bpm_overrides_preset(self, consumer, sample_channel, sample_request):
        sample_request.bpm = 120
        params = consumer.build_generation_params(sample_request, sample_channel)
        assert params.bpm == 120

    def test_user_duration_overrides_preset(self, consumer, sample_channel, sample_request):
        sample_request.duration = 60
        params = consumer.build_generation_params(sample_request, sample_channel)
        assert params.duration == 60

    def test_lyrics_disables_instrumental(self, consumer, sample_channel, sample_request):
        sample_request.lyrics = "[Verse] Hello world"
        params = consumer.build_generation_params(sample_request, sample_channel)
        assert params.instrumental is False
        assert params.lyrics == "[Verse] Hello world"


class TestProcessRequest:
    @pytest.mark.asyncio
    async def test_generates_and_saves_track(
        self, consumer, mock_client, sample_channel, sample_request,
    ):
        session = AsyncMock()
        session.get = AsyncMock(return_value=sample_channel)
        session.add = MagicMock()
        session.execute = AsyncMock()
        session.commit = AsyncMock()

        track = await consumer.process_request(session, sample_request)

        assert track.channel_id == sample_channel.id
        assert track.request_id == sample_request.id
        assert track.file_path.startswith("lofi/")
        assert track.file_path.endswith(".mp3")
        assert track.caption is not None
        assert track.seed is None
        assert track.duration_ms == 180000

    @pytest.mark.asyncio
    async def test_saves_file_to_disk(
        self, consumer, mock_client, sample_channel, sample_request, tmp_path,
    ):
        session = AsyncMock()
        session.get = AsyncMock(return_value=sample_channel)
        session.add = MagicMock()
        session.execute = AsyncMock()
        session.commit = AsyncMock()

        track = await consumer.process_request(session, sample_request)

        full_path = tmp_path / "tracks" / track.file_path
        assert full_path.exists()
        assert full_path.read_bytes() == b"fake-mp3-data"

    @pytest.mark.asyncio
    async def test_raises_on_missing_channel(self, consumer, sample_request):
        session = AsyncMock()
        session.get = AsyncMock(return_value=None)

        with pytest.raises(ValueError, match="Channel .* not found"):
            await consumer.process_request(session, sample_request)


def _make_session_ctx(session):
    """Create a sync-callable that returns an async context manager."""
    ctx = MagicMock()
    ctx.__aenter__ = AsyncMock(return_value=session)
    ctx.__aexit__ = AsyncMock(return_value=False)
    return ctx


class TestPollOnce:
    @pytest.mark.asyncio
    async def test_returns_false_when_no_work(
        self, consumer, mock_session_factory,
    ):
        session = AsyncMock()
        mock_result = MagicMock()
        mock_result.fetchone.return_value = None
        session.execute = AsyncMock(return_value=mock_result)

        consumer.session_factory = lambda: _make_session_ctx(session)

        result = await consumer.poll_once()
        assert result is False

    @pytest.mark.asyncio
    async def test_handles_generation_error(
        self, consumer, mock_session_factory, mock_client,
        sample_channel,
    ):
        request_id = uuid.uuid4()

        mock_client.generate = AsyncMock(
            side_effect=GenerationError("GPU error")
        )

        session = AsyncMock()
        mock_row = MagicMock()
        mock_row.__getitem__ = lambda self, idx: request_id
        mock_result = MagicMock()
        mock_result.fetchone.return_value = mock_row

        request = Request(
            id=request_id,
            channel_id=sample_channel.id,
            status="processing",
        )
        session.execute = AsyncMock(return_value=mock_result)
        session.get = AsyncMock(
            side_effect=[request, sample_channel]
        )
        session.add = MagicMock()
        session.commit = AsyncMock()

        consumer.session_factory = lambda: _make_session_ctx(session)

        result = await consumer.poll_once()
        assert result is True
