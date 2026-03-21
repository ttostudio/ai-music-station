from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from worker.acestep_client import (
    ACEStepClient,
    GenerationError,
    GenerationParams,
    GenerationTimeoutError,
)


@pytest.fixture
def client():
    return ACEStepClient(base_url="http://test:8001", timeout=10, retries=3)


@pytest.fixture
def default_params():
    return GenerationParams(
        caption="test lo-fi beat",
        instrumental=True,
        bpm=80,
        duration=60,
        key="Am",
        seed=42,
    )


class TestGenerationParams:
    def test_defaults(self):
        params = GenerationParams(caption="test")
        assert params.instrumental is True
        assert params.duration == 180
        assert params.num_steps == 8
        assert params.cfg_scale == 7.0
        assert params.seed is None
        assert params.lyrics is None

    def test_custom_values(self):
        params = GenerationParams(
            caption="anime theme",
            lyrics="[Verse] Hello world",
            instrumental=False,
            bpm=140,
            duration=90,
            key="C",
            vocal_language="ja",
            seed=123,
        )
        assert params.caption == "anime theme"
        assert params.lyrics == "[Verse] Hello world"
        assert params.bpm == 140


class TestACEStepClient:
    @pytest.mark.asyncio
    async def test_successful_generation(self, client, default_params):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b"fake-audio-data"
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_cls:
            mock_http = AsyncMock()
            mock_http.post = AsyncMock(return_value=mock_response)
            mock_http.__aenter__ = AsyncMock(return_value=mock_http)
            mock_http.__aexit__ = AsyncMock(return_value=False)
            mock_cls.return_value = mock_http

            result = await client.generate(default_params)

            assert result.audio_data == b"fake-audio-data"
            assert result.sample_rate == 48000
            assert result.seed == 42
            assert result.duration_ms == 60000

            mock_http.post.assert_called_once()
            call_kwargs = mock_http.post.call_args
            payload = call_kwargs.kwargs.get("json") or call_kwargs[1]["json"]
            assert payload["caption"] == "test lo-fi beat"
            assert payload["instrumental"] is True
            assert payload["bpm"] == 80
            assert payload["seed"] == 42

    @pytest.mark.asyncio
    async def test_timeout_raises_error(self, client, default_params):
        with patch("httpx.AsyncClient") as mock_cls:
            mock_http = AsyncMock()
            mock_http.post = AsyncMock(side_effect=httpx.TimeoutException("timeout"))
            mock_http.__aenter__ = AsyncMock(return_value=mock_http)
            mock_http.__aexit__ = AsyncMock(return_value=False)
            mock_cls.return_value = mock_http

            with pytest.raises(GenerationTimeoutError):
                await client.generate(default_params)

    @pytest.mark.asyncio
    async def test_retry_on_503(self, client, default_params):
        mock_response_503 = MagicMock()
        mock_response_503.status_code = 503
        mock_response_503.text = "Service Unavailable"

        mock_response_200 = MagicMock()
        mock_response_200.status_code = 200
        mock_response_200.content = b"audio"
        mock_response_200.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_cls:
            mock_http = AsyncMock()
            mock_http.post = AsyncMock(side_effect=[mock_response_503, mock_response_200])
            mock_http.__aenter__ = AsyncMock(return_value=mock_http)
            mock_http.__aexit__ = AsyncMock(return_value=False)
            mock_cls.return_value = mock_http

            result = await client.generate(default_params)
            assert result.audio_data == b"audio"
            assert mock_http.post.call_count == 2

    @pytest.mark.asyncio
    async def test_exhausted_retries_raises(self, client, default_params):
        mock_response_503 = MagicMock()
        mock_response_503.status_code = 503
        mock_response_503.text = "Service Unavailable"

        with patch("httpx.AsyncClient") as mock_cls:
            mock_http = AsyncMock()
            mock_http.post = AsyncMock(return_value=mock_response_503)
            mock_http.__aenter__ = AsyncMock(return_value=mock_http)
            mock_http.__aexit__ = AsyncMock(return_value=False)
            mock_cls.return_value = mock_http

            with pytest.raises(GenerationError):
                await client.generate(default_params)
            assert mock_http.post.call_count == 3

    @pytest.mark.asyncio
    async def test_random_seed_when_none(self, client):
        params = GenerationParams(caption="test", seed=None)

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b"audio"
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_cls:
            mock_http = AsyncMock()
            mock_http.post = AsyncMock(return_value=mock_response)
            mock_http.__aenter__ = AsyncMock(return_value=mock_http)
            mock_http.__aexit__ = AsyncMock(return_value=False)
            mock_cls.return_value = mock_http

            result = await client.generate(params)
            assert isinstance(result.seed, int)

    @pytest.mark.asyncio
    async def test_lyrics_included_in_payload(self, client):
        params = GenerationParams(
            caption="anime",
            lyrics="[Verse] Test lyrics",
            vocal_language="ja",
            seed=1,
        )

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b"audio"
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_cls:
            mock_http = AsyncMock()
            mock_http.post = AsyncMock(return_value=mock_response)
            mock_http.__aenter__ = AsyncMock(return_value=mock_http)
            mock_http.__aexit__ = AsyncMock(return_value=False)
            mock_cls.return_value = mock_http

            await client.generate(params)
            call_kwargs = mock_http.post.call_args
            payload = call_kwargs.kwargs.get("json") or call_kwargs[1]["json"]
            assert payload["lyrics"] == "[Verse] Test lyrics"
            assert payload["vocal_language"] == "ja"
