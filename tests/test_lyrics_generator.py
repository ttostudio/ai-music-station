"""歌詞・曲名自動生成モジュールのテスト"""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, patch

import pytest

from worker.lyrics_generator import LyricsGenerator, LyricsResult


def _make_cli_output(data: dict) -> bytes:
    """claude CLI の --output-format json 出力を生成"""
    return json.dumps(
        {"type": "result", "result": json.dumps(data, ensure_ascii=False)},
    ).encode()


@pytest.fixture
def lyrics_json():
    return {
        "title": "雨音のメロディ",
        "caption": "lo-fi hip hop, rainy day, mellow piano, chill beats",
        "lyrics": "[Verse]\n雨が降る街角で\n\n[Chorus]\n雨音のメロディ",
    }


@pytest.fixture
def lyrics_json_starry():
    return {
        "title": "星空の下で",
        "caption": "ambient, starry night, soft synth pads",
        "lyrics": "[Verse]\n星空の下で\n\n[Chorus]\n輝く光",
    }


class TestLyricsGenerator:
    @pytest.mark.asyncio
    async def test_generate_success(self, lyrics_json):
        """正常系: claude CLIから歌詞・曲名を生成"""
        mock_proc = AsyncMock()
        mock_proc.communicate.return_value = (
            _make_cli_output(lyrics_json), b"",
        )
        mock_proc.returncode = 0

        with patch("worker.lyrics_generator.asyncio.create_subprocess_exec",
                    return_value=mock_proc) as mock_exec:
            generator = LyricsGenerator(claude_command="claude")
            result = await generator.generate(
                mood="雨の日の切ない気分",
                channel_name="LoFi Beats",
                channel_description="チルなビート",
            )

        assert isinstance(result, LyricsResult)
        assert result.title == "雨音のメロディ"
        assert "lo-fi" in result.caption
        assert "[Verse]" in result.lyrics

        mock_exec.assert_called_once()
        call_args = mock_exec.call_args[0]
        assert call_args[0] == "claude"
        assert "-p" in call_args
        assert "--output-format" in call_args
        assert "json" in call_args

    @pytest.mark.asyncio
    async def test_generate_with_embedded_json(self, lyrics_json_starry):
        """レスポンスにJSON以外のテキストが含まれていてもパース可能"""
        raw_text = f"以下が結果です:\n{json.dumps(lyrics_json_starry, ensure_ascii=False)}"
        output = json.dumps(
            {"type": "result", "result": raw_text},
        ).encode()

        mock_proc = AsyncMock()
        mock_proc.communicate.return_value = (output, b"")
        mock_proc.returncode = 0

        with patch("worker.lyrics_generator.asyncio.create_subprocess_exec",
                    return_value=mock_proc):
            generator = LyricsGenerator()
            result = await generator.generate(
                mood="星空",
                channel_name="Ambient",
            )

        assert result.title == "星空の下で"
        assert "ambient" in result.caption

    @pytest.mark.asyncio
    async def test_generate_fallback_on_cli_error(self):
        """CLI失敗時のフォールバック"""
        mock_proc = AsyncMock()
        mock_proc.communicate.return_value = (b"", b"command not found")
        mock_proc.returncode = 1

        with patch("worker.lyrics_generator.asyncio.create_subprocess_exec",
                    return_value=mock_proc):
            generator = LyricsGenerator()
            result = await generator.generate(
                mood="朝の爽やかさ",
                channel_name="Morning Chill",
            )

        assert result.title == "朝の爽やかさ"
        assert "Morning Chill" in result.caption
        assert "[Verse]" in result.lyrics

    @pytest.mark.asyncio
    async def test_generate_fallback_on_invalid_json(self):
        """不正JSONレスポンス時のフォールバック"""
        output = json.dumps(
            {"type": "result", "result": "これはJSONではありません"},
        ).encode()

        mock_proc = AsyncMock()
        mock_proc.communicate.return_value = (output, b"")
        mock_proc.returncode = 0

        with patch("worker.lyrics_generator.asyncio.create_subprocess_exec",
                    return_value=mock_proc):
            generator = LyricsGenerator()
            result = await generator.generate(
                mood="夕暮れ",
                channel_name="Sunset FM",
            )

        assert result.title == "夕暮れ"
        assert "Sunset FM" in result.caption

    @pytest.mark.asyncio
    async def test_generate_fallback_on_timeout(self):
        """タイムアウト時のフォールバック"""
        mock_proc = AsyncMock()
        mock_proc.communicate.side_effect = TimeoutError()

        with patch("worker.lyrics_generator.asyncio.create_subprocess_exec",
                    return_value=mock_proc):
            generator = LyricsGenerator()
            result = await generator.generate(
                mood="深夜のドライブ",
                channel_name="Night Drive",
            )

        assert result.title == "深夜のドライブ"
        assert "Night Drive" in result.caption

    @pytest.mark.asyncio
    async def test_prompt_contains_channel_context(self, lyrics_json):
        """プロンプトにチャンネル情報が含まれることを確認"""
        mock_proc = AsyncMock()
        mock_proc.communicate.return_value = (
            _make_cli_output(lyrics_json), b"",
        )
        mock_proc.returncode = 0

        with patch("worker.lyrics_generator.asyncio.create_subprocess_exec",
                    return_value=mock_proc) as mock_exec:
            generator = LyricsGenerator()
            await generator.generate(
                mood="テスト",
                channel_name="Jazz Night",
                channel_description="夜のジャズ",
            )

        call_args = mock_exec.call_args[0]
        prompt_text = call_args[2]  # claude -p <prompt>
        assert "Jazz Night" in prompt_text
        assert "夜のジャズ" in prompt_text
        assert "テスト" in prompt_text

    @pytest.mark.asyncio
    async def test_existing_titles_included_in_prompt(self, lyrics_json):
        """既存タイトルがプロンプトに含まれることを確認"""
        mock_proc = AsyncMock()
        mock_proc.communicate.return_value = (
            _make_cli_output(lyrics_json), b"",
        )
        mock_proc.returncode = 0

        with patch("worker.lyrics_generator.asyncio.create_subprocess_exec",
                    return_value=mock_proc) as mock_exec:
            generator = LyricsGenerator()
            await generator.generate(
                mood="テスト",
                channel_name="Jazz Night",
                channel_description="夜のジャズ",
                existing_titles=["夜風のささやき", "月明かりのワルツ"],
            )

        call_args = mock_exec.call_args[0]
        prompt_text = call_args[2]  # claude -p <prompt>
        assert "夜風のささやき" in prompt_text
        assert "月明かりのワルツ" in prompt_text
        assert "ユニークなタイトル" in prompt_text

    @pytest.mark.asyncio
    async def test_no_existing_titles_section_when_empty(self, lyrics_json):
        """既存タイトルがない場合はプロンプトに重複防止セクションが含まれない"""
        mock_proc = AsyncMock()
        mock_proc.communicate.return_value = (
            _make_cli_output(lyrics_json), b"",
        )
        mock_proc.returncode = 0

        with patch("worker.lyrics_generator.asyncio.create_subprocess_exec",
                    return_value=mock_proc) as mock_exec:
            generator = LyricsGenerator()
            await generator.generate(
                mood="テスト",
                channel_name="Jazz Night",
            )

        call_args = mock_exec.call_args[0]
        prompt_text = call_args[2]
        assert "ユニークなタイトル" not in prompt_text
