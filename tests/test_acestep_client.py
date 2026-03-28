from __future__ import annotations

from pathlib import Path
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
from api.services.acestep_client import AceStepError, AceStepTimeoutError


@pytest.fixture
def client():
    return ACEStepClient(base_url="http://test:8001", timeout=10)


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
    """Create a mock chat completions response matching ACE-Step's actual format."""
    resp = MagicMock()
    resp.status_code = 200
    resp.raise_for_status = MagicMock()
    resp.json = MagicMock(return_value={
        "id": "chatcmpl-test",
        "object": "chat.completion",
        "model": "ace-step-v1.5",
        "choices": [{
            "index": 0,
            "message": {
                "role": "assistant",
                "content": "## Metadata\n**Caption:** test",
                "audio": [{
                    "type": "audio_url",
                    "audio_url": {
                        "url": f"data:audio/mpeg;base64,{audio_b64}",
                    },
                }],
            },
            "finish_reason": "stop",
        }],
        "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
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
    async def test_successful_generation(self, client, tmp_path):
        """generate_sync が成功した場合にファイルを書き込み result を返す"""
        mock_response = _make_chat_response()
        params = {"prompt": "test lo-fi beat", "audio_duration": 60}
        dest = tmp_path / "output.mp3"

        mock_http = AsyncMock()
        mock_http.post = AsyncMock(return_value=mock_response)
        client._client = mock_http

        result = await client.generate_sync(params, dest)

        assert dest.exists()
        assert dest.read_bytes() == b"fake-audio-data"
        assert result.status == "completed"
        assert result.audio_path == str(dest)
        mock_http.post.assert_called_once()
        call_args = mock_http.post.call_args
        assert "/v1/chat/completions" in call_args.args[0]
        payload = call_args.kwargs.get("json") or call_args[1]["json"]
        assert payload["model"] in ("ace-step-v1.5-turbo", "ace-step-v1.5")
        assert "test lo-fi beat" in payload["messages"][0]["content"]

    @pytest.mark.asyncio
    async def test_timeout_raises_error(self, client, tmp_path):
        """タイムアウト時に AceStepTimeoutError が送出される"""
        params = {"prompt": "test", "audio_duration": 10}
        dest = tmp_path / "output.mp3"

        mock_http = AsyncMock()
        mock_http.post = AsyncMock(side_effect=httpx.TimeoutException("timeout"))
        client._client = mock_http

        with pytest.raises(AceStepTimeoutError):
            await client.generate_sync(params, dest)

    @pytest.mark.asyncio
    async def test_connect_error_raises_generation_error(self, client, tmp_path):
        """接続失敗時に AceStepError が送出される"""
        params = {"prompt": "test", "audio_duration": 10}
        dest = tmp_path / "output.mp3"

        mock_http = AsyncMock()
        mock_http.post = AsyncMock(side_effect=httpx.ConnectError("refused"))
        client._client = mock_http

        with pytest.raises(AceStepError):
            await client.generate_sync(params, dest)

    @pytest.mark.asyncio
    async def test_queue_full_raises_error(self, client, tmp_path):
        """HTTP 429 で AceStepQueueFullError が送出される"""
        from api.services.acestep_client import AceStepQueueFullError

        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_response.raise_for_status = MagicMock()

        params = {"prompt": "test", "audio_duration": 10}
        dest = tmp_path / "output.mp3"

        mock_http = AsyncMock()
        mock_http.post = AsyncMock(return_value=mock_response)
        client._client = mock_http

        with pytest.raises(AceStepQueueFullError):
            await client.generate_sync(params, dest)

    @pytest.mark.asyncio
    async def test_empty_choices_raises_error(self, client, tmp_path):
        """choices が空の場合に AceStepError が送出される"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        mock_response.json = MagicMock(return_value={"choices": []})

        params = {"prompt": "test", "audio_duration": 10}
        dest = tmp_path / "output.mp3"

        mock_http = AsyncMock()
        mock_http.post = AsyncMock(return_value=mock_response)
        client._client = mock_http

        with pytest.raises(AceStepError):
            await client.generate_sync(params, dest)
