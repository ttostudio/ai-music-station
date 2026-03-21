from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from worker.acestep_client import (
    ACEStepClient,
    GenerationError,
    GenerationParams,
    GenerationTimeoutError,
    _build_prompt,
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


def _make_chat_response(audio_b64: str = "ZmFrZS1hdWRpby1kYXRh") -> MagicMock:
    """Create a mock chat completions response with base64 audio."""
    resp = MagicMock()
    resp.status_code = 200
    resp.raise_for_status = MagicMock()
    resp.json = MagicMock(return_value={
        "choices": [{
            "message": {
                "content": json.dumps({"audio_base64": audio_b64}),
            },
        }],
    })
    return resp


class TestBuildPrompt:
    def test_basic(self):
        params = GenerationParams(caption="chill lo-fi")
        prompt = _build_prompt(params)
        assert "chill lo-fi" in prompt
        assert "Instrumental" in prompt

    def test_with_bpm_and_key(self):
        params = GenerationParams(caption="jazz", bpm=120, key="Dm")
        prompt = _build_prompt(params)
        assert "BPM: 120" in prompt
        assert "Key: Dm" in prompt

    def test_with_lyrics(self):
        params = GenerationParams(caption="anime", lyrics="[Verse] Hello", instrumental=False)
        prompt = _build_prompt(params)
        assert "Lyrics: [Verse] Hello" in prompt
        assert "Instrumental" not in prompt


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
        mock_response = _make_chat_response()

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
            assert "/v1/chat/completions" in call_kwargs.args[0]
            payload = call_kwargs.kwargs.get("json") or call_kwargs[1]["json"]
            assert payload["model"] == "ace-step-v1.5"
            assert len(payload["messages"]) == 1
            assert "test lo-fi beat" in payload["messages"][0]["content"]

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

        mock_response_200 = _make_chat_response()

        with patch("httpx.AsyncClient") as mock_cls:
            mock_http = AsyncMock()
            mock_http.post = AsyncMock(side_effect=[mock_response_503, mock_response_200])
            mock_http.__aenter__ = AsyncMock(return_value=mock_http)
            mock_http.__aexit__ = AsyncMock(return_value=False)
            mock_cls.return_value = mock_http

            result = await client.generate(default_params)
            assert result.audio_data == b"fake-audio-data"
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
        mock_response = _make_chat_response()

        with patch("httpx.AsyncClient") as mock_cls:
            mock_http = AsyncMock()
            mock_http.post = AsyncMock(return_value=mock_response)
            mock_http.__aenter__ = AsyncMock(return_value=mock_http)
            mock_http.__aexit__ = AsyncMock(return_value=False)
            mock_cls.return_value = mock_http

            result = await client.generate(params)
            assert isinstance(result.seed, int)

    @pytest.mark.asyncio
    async def test_audio_url_download(self, client, default_params):
        """Test extraction when response contains audio_url instead of base64."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        mock_response.json = MagicMock(return_value={
            "choices": [{
                "message": {
                    "content": json.dumps({"audio_url": "http://test/audio.flac"}),
                },
            }],
        })

        with patch("httpx.AsyncClient") as mock_cls, \
             patch("httpx.Client") as mock_sync_cls:
            mock_http = AsyncMock()
            mock_http.post = AsyncMock(return_value=mock_response)
            mock_http.__aenter__ = AsyncMock(return_value=mock_http)
            mock_http.__aexit__ = AsyncMock(return_value=False)
            mock_cls.return_value = mock_http

            mock_sync = MagicMock()
            mock_dl_resp = MagicMock()
            mock_dl_resp.content = b"downloaded-audio"
            mock_dl_resp.raise_for_status = MagicMock()
            mock_sync.get = MagicMock(return_value=mock_dl_resp)
            mock_sync.__enter__ = MagicMock(return_value=mock_sync)
            mock_sync.__exit__ = MagicMock(return_value=False)
            mock_sync_cls.return_value = mock_sync

            result = await client.generate(default_params)
            assert result.audio_data == b"downloaded-audio"
