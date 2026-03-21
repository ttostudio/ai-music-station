"""歌詞・曲名の自動生成モジュール（claude CLI統合）"""

from __future__ import annotations

import asyncio
import json
import logging
import re
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class LyricsResult:
    """歌詞生成の結果"""

    title: str
    caption: str
    lyrics: str


class LyricsGenerator:
    """ローカルの claude CLI を使って歌詞・曲名を生成する"""

    def __init__(self, claude_command: str = "claude"):
        self.claude_command = claude_command

    async def generate(
        self, mood: str, channel_name: str,
        channel_description: str | None = None,
    ) -> LyricsResult:
        """雰囲気から歌詞・曲名・キャプションを生成する

        Args:
            mood: 楽曲の雰囲気（例: "雨の日の切ない気分"）
            channel_name: チャンネル名
            channel_description: チャンネルの説明

        Returns:
            LyricsResult: 生成された曲名・キャプション・歌詞
        """
        prompt = self._build_prompt(mood, channel_name, channel_description)

        try:
            proc = await asyncio.create_subprocess_exec(
                self.claude_command, "-p", prompt,
                "--output-format", "json",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(), timeout=120,
            )

            if proc.returncode != 0:
                raise RuntimeError(
                    f"claude CLI failed: {stderr.decode()}",
                )

            # claude --output-format json は {"type":"result","result":"..."} を返す
            output = json.loads(stdout.decode())
            text = output.get("result", stdout.decode())

            return self._parse_response(text)
        except (
            RuntimeError, json.JSONDecodeError, KeyError,
            TimeoutError, OSError,
        ) as e:
            logger.warning(
                "歌詞生成に失敗しました（フォールバック使用）: %s", e,
            )
            return LyricsResult(
                title=mood,
                caption=f"{mood}, {channel_name}",
                lyrics=f"[Verse]\n{mood}",
            )

    def _build_prompt(
        self, mood: str, channel_name: str,
        channel_description: str | None,
    ) -> str:
        return (
            "あなたは音楽の作詞家です。"
            "以下の雰囲気に合った楽曲を作成してください。\n\n"
            f"チャンネル: {channel_name}\n"
            f"チャンネル説明: {channel_description or ''}\n"
            f"雰囲気: {mood}\n\n"
            "以下のJSON形式のみで回答してください"
            "（他のテキストは不要）:\n"
            "{\n"
            '  "title": "曲名（日本語）",\n'
            '  "caption": "ACE-Step用の英語キャプション'
            "（ジャンル、楽器、雰囲気を含む、100語以内）\",\n"
            '  "lyrics": "[Verse 1]\\n歌詞...\\n\\n[Chorus]\\n歌詞...'
            '\\n\\n[Verse 2]\\n歌詞...\\n\\n[Chorus]\\n歌詞..."\n'
            "}"
        )

    def _parse_response(self, text: str) -> LyricsResult:
        """レスポンスからJSON部分を抽出してパースする"""
        match = re.search(r'\{[^{}]*"title"[^{}]*\}', text, re.DOTALL)
        data = json.loads(match.group()) if match else json.loads(text)

        return LyricsResult(
            title=data["title"],
            caption=data["caption"],
            lyrics=data["lyrics"],
        )
