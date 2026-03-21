"""歌詞・曲名自動生成のテスト"""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

from worker.lyrics_generator import LyricsGenerator, LyricsResult


@pytest.fixture
def mock_anthropic_response():
    """Claude APIのモックレスポンス"""
    data = {
        "title": "夜の散歩道",
        "caption": "lo-fi hip hop beat, chill, mellow piano, rainy night atmosphere",
        "lyrics": "[Verse]\n夜の街を歩く\n[Chorus]\n静かな時間",
    }
    content_block = MagicMock()
    content_block.text = json.dumps(data, ensure_ascii=False)
    message = MagicMock()
    message.content = [content_block]
    return message


@pytest.fixture
def generator():
    return LyricsGenerator(api_key="test-key")


class TestLyricsGenerator:
    def test_generate_returns_lyrics_result(self, generator, mock_anthropic_response):
        with patch.object(
            generator.client.messages, "create", return_value=mock_anthropic_response
        ):
            result = generator.generate(
                mood="雨の夜、しっとりした気分",
                channel_name="LoFi ビーツ",
                channel_description="チルなローファイ",
                prompt_template="lo-fi hip hop beat",
            )
            assert isinstance(result, LyricsResult)
            assert result.title == "夜の散歩道"
            assert "lo-fi" in result.caption
            assert "[Verse]" in result.lyrics

    def test_generate_instrumental_clears_lyrics(self, generator, mock_anthropic_response):
        with patch.object(
            generator.client.messages, "create", return_value=mock_anthropic_response
        ):
            result = generator.generate(
                mood="リラックス",
                channel_name="LoFi ビーツ",
                channel_description="チルなローファイ",
                instrumental=True,
            )
            assert result.lyrics == ""

    def test_generate_handles_json_in_code_block(self, generator):
        data = {
            "title": "Test Song",
            "caption": "test caption",
            "lyrics": "[Verse] test",
        }
        content_block = MagicMock()
        content_block.text = f"```json\n{json.dumps(data)}\n```"
        message = MagicMock()
        message.content = [content_block]

        with patch.object(
            generator.client.messages, "create", return_value=message
        ):
            result = generator.generate(
                mood="happy",
                channel_name="Test",
                channel_description="Test channel",
            )
            assert result.title == "Test Song"

    def test_generate_passes_preference_hint(self, generator, mock_anthropic_response):
        with patch.object(
            generator.client.messages, "create", return_value=mock_anthropic_response
        ) as mock_create:
            generator.generate(
                mood="chill",
                channel_name="LoFi",
                channel_description="Chill beats",
                preference_hint="BPM 70-80, ピアノ主体の曲が人気",
            )
            call_args = mock_create.call_args
            user_msg = call_args.kwargs["messages"][0]["content"]
            assert "リスナーの好み" in user_msg
            assert "BPM 70-80" in user_msg


class TestQueueConsumerWithLyrics:
    """QueueConsumer の歌詞生成統合テスト"""

    def test_build_params_with_generated_caption(self, sample_channel, sample_request):
        from worker.queue_consumer import QueueConsumer

        consumer = QueueConsumer(
            session_factory=MagicMock(),
            client=MagicMock(),
            tracks_dir="/tmp/test-tracks",
            worker_id="test",
        )
        params = consumer.build_generation_params(
            sample_request, sample_channel,
            generated_caption="AI generated caption",
            generated_lyrics="[Verse] AI lyrics",
        )
        assert params.caption == "AI generated caption"
        assert params.lyrics == "[Verse] AI lyrics"
        assert params.instrumental is False  # 歌詞があるのでFalse

    def test_build_params_without_generated_uses_default(
        self, sample_channel, sample_request,
    ):
        from worker.queue_consumer import QueueConsumer

        consumer = QueueConsumer(
            session_factory=MagicMock(),
            client=MagicMock(),
            tracks_dir="/tmp/test-tracks",
            worker_id="test",
        )
        params = consumer.build_generation_params(sample_request, sample_channel)
        assert "lo-fi" in params.caption.lower()
        assert params.lyrics is None
