"""歌詞・曲名の自動生成モジュール（Claude API統合）"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass

import anthropic

from worker.config import settings

logger = logging.getLogger(__name__)


@dataclass
class LyricsResult:
    """歌詞生成の結果"""

    title: str
    caption: str
    lyrics: str


class LyricsGenerator:
    """Claude APIを使用して雰囲気から歌詞・曲名・キャプションを生成する"""

    def __init__(self, api_key: str | None = None):
        self.client = anthropic.Anthropic(
            api_key=api_key or settings.anthropic_api_key,
        )

    def generate(
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
        channel_context = f"チャンネル「{channel_name}」"
        if channel_description:
            channel_context += f"（{channel_description}）"

        prompt = (
            f"{channel_context}向けの楽曲を作成します。\n"
            f"雰囲気: {mood}\n\n"
            "以下のJSON形式で、楽曲の曲名・音楽生成用キャプション"
            "・歌詞を生成してください。\n"
            "歌詞は [Verse], [Chorus], [Bridge] などの"
            "セクションタグを含めてください。\n"
            "キャプションは音楽生成AIへの指示として使われるため、"
            "英語で音楽ジャンル・楽器・雰囲気を簡潔に記述してください。\n\n"
            "```json\n"
            "{\n"
            '  "title": "曲名（日本語）",\n'
            '  "caption": "music generation caption in English, '
            'describing genre, instruments, mood",\n'
            '  "lyrics": "[Verse]\\n歌詞の内容...\\n\\n[Chorus]\\n..."\n'
            "}\n"
            "```\n\n"
            "JSONのみを返してください。説明は不要です。"
        )

        try:
            message = self.client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=1024,
                messages=[{"role": "user", "content": prompt}],
            )

            response_text = message.content[0].text
            if "```json" in response_text:
                response_text = (
                    response_text.split("```json")[1].split("```")[0]
                )
            elif "```" in response_text:
                response_text = (
                    response_text.split("```")[1].split("```")[0]
                )

            data = json.loads(response_text.strip())

            return LyricsResult(
                title=data["title"],
                caption=data["caption"],
                lyrics=data["lyrics"],
            )
        except (
            anthropic.APIError, json.JSONDecodeError, KeyError, IndexError,
        ) as e:
            logger.warning(
                "歌詞生成に失敗しました（フォールバック使用）: %s", e,
            )
            return LyricsResult(
                title=mood,
                caption=f"{mood}, {channel_name}",
                lyrics=f"[Verse]\n{mood}",
            )
