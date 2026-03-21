"""歌詞・曲名自動生成モジュールのテスト"""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

from worker.lyrics_generator import LyricsGenerator, LyricsResult


@pytest.fixture
def mock_anthropic_response():
    """Claude APIの正常レスポンスをモック"""
    data = {
        "title": "雨音のメロディ",
        "caption": "lo-fi hip hop, rainy day, mellow piano, chill beats",
        "lyrics": "[Verse]\n雨が降る街角で\n\n[Chorus]\n雨音のメロディ",
    }
    content_block = MagicMock()
    content_block.text = json.dumps(data, ensure_ascii=False)
    message = MagicMock()
    message.content = [content_block]
    return message


@pytest.fixture
def mock_anthropic_response_with_codeblock():
    """コードブロック付きレスポンスをモック"""
    data = {
        "title": "星空の下で",
        "caption": "ambient, starry night, soft synth pads",
        "lyrics": "[Verse]\n星空の下で\n\n[Chorus]\n輝く光",
    }
    content_block = MagicMock()
    content_block.text = (
        f"```json\n{json.dumps(data, ensure_ascii=False)}\n```"
    )
    message = MagicMock()
    message.content = [content_block]
    return message


class TestLyricsGenerator:
    @patch("worker.lyrics_generator.anthropic.Anthropic")
    def test_generate_success(
        self, mock_anthropic_cls, mock_anthropic_response,
    ):
        """正常系: Claude APIから歌詞・曲名を生成"""
        mock_client = MagicMock()
        mock_client.messages.create.return_value = (
            mock_anthropic_response
        )
        mock_anthropic_cls.return_value = mock_client

        generator = LyricsGenerator(api_key="test-key")
        result = generator.generate(
            mood="雨の日の切ない気分",
            channel_name="LoFi Beats",
            channel_description="チルなビート",
        )

        assert isinstance(result, LyricsResult)
        assert result.title == "雨音のメロディ"
        assert "lo-fi" in result.caption
        assert "[Verse]" in result.lyrics

        mock_client.messages.create.assert_called_once()
        call_kwargs = mock_client.messages.create.call_args.kwargs
        assert call_kwargs["model"] == "claude-haiku-4-5-20251001"
        assert call_kwargs["max_tokens"] == 1024

    @patch("worker.lyrics_generator.anthropic.Anthropic")
    def test_generate_with_codeblock(
        self, mock_anthropic_cls,
        mock_anthropic_response_with_codeblock,
    ):
        """コードブロック付きレスポンスを正しくパース"""
        mock_client = MagicMock()
        mock_client.messages.create.return_value = (
            mock_anthropic_response_with_codeblock
        )
        mock_anthropic_cls.return_value = mock_client

        generator = LyricsGenerator(api_key="test-key")
        result = generator.generate(
            mood="星空",
            channel_name="Ambient",
        )

        assert result.title == "星空の下で"
        assert "ambient" in result.caption

    @patch("worker.lyrics_generator.anthropic.Anthropic")
    def test_generate_fallback_on_api_error(
        self, mock_anthropic_cls,
    ):
        """API失敗時のフォールバック"""
        import anthropic as anthropic_mod

        mock_client = MagicMock()
        mock_client.messages.create.side_effect = (
            anthropic_mod.APIError(
                message="Service unavailable",
                request=MagicMock(),
                body=None,
            )
        )
        mock_anthropic_cls.return_value = mock_client

        generator = LyricsGenerator(api_key="test-key")
        result = generator.generate(
            mood="朝の爽やかさ",
            channel_name="Morning Chill",
        )

        assert result.title == "朝の爽やかさ"
        assert "Morning Chill" in result.caption
        assert "[Verse]" in result.lyrics

    @patch("worker.lyrics_generator.anthropic.Anthropic")
    def test_generate_fallback_on_invalid_json(
        self, mock_anthropic_cls,
    ):
        """不正JSONレスポンス時のフォールバック"""
        content_block = MagicMock()
        content_block.text = "これはJSONではありません"
        message = MagicMock()
        message.content = [content_block]

        mock_client = MagicMock()
        mock_client.messages.create.return_value = message
        mock_anthropic_cls.return_value = mock_client

        generator = LyricsGenerator(api_key="test-key")
        result = generator.generate(
            mood="夕暮れ",
            channel_name="Sunset FM",
        )

        assert result.title == "夕暮れ"
        assert "Sunset FM" in result.caption

    @patch("worker.lyrics_generator.anthropic.Anthropic")
    def test_prompt_contains_channel_context(
        self, mock_anthropic_cls, mock_anthropic_response,
    ):
        """プロンプトにチャンネル情報が含まれることを確認"""
        mock_client = MagicMock()
        mock_client.messages.create.return_value = (
            mock_anthropic_response
        )
        mock_anthropic_cls.return_value = mock_client

        generator = LyricsGenerator(api_key="test-key")
        generator.generate(
            mood="テスト",
            channel_name="Jazz Night",
            channel_description="夜のジャズ",
        )

        call_kwargs = mock_client.messages.create.call_args.kwargs
        prompt_text = call_kwargs["messages"][0]["content"]
        assert "Jazz Night" in prompt_text
        assert "夜のジャズ" in prompt_text
        assert "テスト" in prompt_text
