"""Claude API を使った歌詞・曲名・キャプションの自動生成"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass

import anthropic

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """\
あなたはAI音楽ステーションの作詞・作曲アシスタントです。
指定されたムード・チャンネルの特徴に合わせて、曲名・キャプション・歌詞を生成してください。

ルール:
- title: 曲名（短く印象的に、日本語または英語）
- caption: ACE-Step音楽生成AIへのプロンプト（英語、音楽ジャンル・楽器・雰囲気を具体的に記述）
- lyrics: 歌詞（[Verse], [Chorus] などのタグ付き。instrumentalチャンネルの場合は空文字）

JSON形式で出力してください:
{"title": "...", "caption": "...", "lyrics": "..."}
"""


@dataclass(frozen=True)
class LyricsResult:
    title: str
    caption: str
    lyrics: str


class LyricsGenerator:
    """Claude API で歌詞・曲名・キャプションを生成する"""

    def __init__(self, api_key: str, model: str = "claude-sonnet-4-20250514"):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model

    def generate(
        self,
        mood: str,
        channel_name: str,
        channel_description: str,
        *,
        instrumental: bool = False,
        prompt_template: str = "",
        preference_hint: str = "",
    ) -> LyricsResult:
        """ムードとチャンネル情報から歌詞・曲名・キャプションを生成する"""
        user_content = (
            f"チャンネル: {channel_name}\n"
            f"チャンネル説明: {channel_description}\n"
            f"ムード: {mood}\n"
            f"インストゥルメンタル: {'はい' if instrumental else 'いいえ'}\n"
            f"参考プロンプト: {prompt_template}\n"
        )
        if preference_hint:
            user_content += f"リスナーの好み: {preference_hint}\n"

        user_content += (
            "\n上記の情報を元に、曲名・キャプション・歌詞をJSON形式で生成してください。"
        )

        logger.info("Claude API で歌詞生成: mood=%s channel=%s", mood, channel_name)

        message = self.client.messages.create(
            model=self.model,
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_content}],
        )

        raw = message.content[0].text
        # JSON部分を抽出（```json ... ``` で囲まれている場合に対応）
        if "```json" in raw:
            raw = raw.split("```json")[1].split("```")[0]
        elif "```" in raw:
            raw = raw.split("```")[1].split("```")[0]

        data = json.loads(raw.strip())

        return LyricsResult(
            title=data.get("title", ""),
            caption=data.get("caption", ""),
            lyrics=data.get("lyrics", "") if not instrumental else "",
        )
