"""AI Podcast — ブログ記事をTTSでポッドキャストエピソードに変換する"""

from __future__ import annotations

import logging
import re
import uuid
from dataclasses import dataclass
from pathlib import Path

import aiohttp
import edge_tts

logger = logging.getLogger(__name__)

TECH_BLOG_API = "http://localhost:3100/api"
TTS_VOICE = "ja-JP-NanamiNeural"
PODCAST_CHANNEL_SLUG = "podcast"


@dataclass
class PodcastEpisode:
    """生成されたポッドキャストエピソード"""

    article_id: str
    article_slug: str
    title: str
    description: str
    audio_path: str
    duration_ms: int


def strip_markdown(text: str) -> str:
    """Markdown記法を除去して読み上げ用プレーンテキストにする"""
    text = re.sub(r"```[\s\S]*?```", "", text)
    text = re.sub(r"`[^`]+`", "", text)
    text = re.sub(r"^#{1,6}\s+", "", text, flags=re.MULTILINE)
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    text = re.sub(r"!\[([^\]]*)\]\([^)]+\)", "", text)
    text = re.sub(r"(\*{1,3}|_{1,3})", "", text)
    text = re.sub(r"^[>|]\s?", "", text, flags=re.MULTILINE)
    text = re.sub(r"^[-*+]\s", "", text, flags=re.MULTILINE)
    text = re.sub(r"^\d+\.\s", "", text, flags=re.MULTILINE)
    text = re.sub(r"\|.*\|", "", text)
    text = re.sub(r"^-{3,}$", "", text, flags=re.MULTILINE)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


async def fetch_articles() -> list[dict]:
    """ai-tech-blogから公開記事一覧を取得"""
    async with aiohttp.ClientSession() as session, session.get(f"{TECH_BLOG_API}/articles") as resp:
        resp.raise_for_status()
        data = await resp.json()
        return data.get("data", [])


async def fetch_article(slug: str) -> dict:
    """記事の全文を取得"""
    async with (
        aiohttp.ClientSession() as session,
        session.get(f"{TECH_BLOG_API}/articles/{slug}") as resp,
    ):
        resp.raise_for_status()
        data = await resp.json()
        return data.get("data", {})


def build_narration_text(article: dict) -> str:
    """記事をナレーション原稿に変換"""
    title = article.get("title", "")
    content = article.get("content", "")
    plain = strip_markdown(content)

    intro = f"ttoStudio AI Tech Blog。今回の記事は、「{title}」です。"
    outro = "以上、ttoStudio AI Tech Blog でした。お聴きいただきありがとうございます。"

    return f"{intro}\n\n{plain}\n\n{outro}"


async def generate_tts_audio(text: str, output_path: str) -> None:
    """Edge TTSでテキストからMP3音声を生成"""
    communicate = edge_tts.Communicate(text, TTS_VOICE)
    await communicate.save(output_path)
    logger.info("TTS音声生成完了: %s", output_path)


async def get_audio_duration_ms(file_path: str) -> int:
    """MP3ファイルの長さをミリ秒で概算する（ビットレートベース）"""
    size = Path(file_path).stat().st_size
    bitrate_bps = 48000  # Edge TTS default ~48kbps
    duration_s = (size * 8) / bitrate_bps
    return int(duration_s * 1000)


async def generate_episode(
    article_slug: str,
    output_dir: str,
) -> PodcastEpisode:
    """記事スラッグからポッドキャストエピソードを生成する

    Args:
        article_slug: ai-tech-blog の記事スラッグ
        output_dir: 音声ファイル出力ディレクトリ

    Returns:
        PodcastEpisode: 生成されたエピソード情報
    """
    article = await fetch_article(article_slug)
    if not article:
        raise ValueError(f"記事が見つかりません: {article_slug}")

    title = article.get("title", article_slug)
    excerpt = article.get("excerpt", "")[:200]

    narration = build_narration_text(article)

    out_dir = Path(output_dir) / PODCAST_CHANNEL_SLUG
    out_dir.mkdir(parents=True, exist_ok=True)

    file_id = uuid.uuid4().hex[:8]
    filename = f"ep_{article_slug}_{file_id}.mp3"
    audio_path = str(out_dir / filename)

    await generate_tts_audio(narration, audio_path)

    duration_ms = await get_audio_duration_ms(audio_path)

    return PodcastEpisode(
        article_id=article.get("id", ""),
        article_slug=article_slug,
        title=title,
        description=excerpt,
        audio_path=audio_path,
        duration_ms=duration_ms,
    )


async def generate_all_episodes(
    output_dir: str,
    existing_slugs: set[str] | None = None,
) -> list[PodcastEpisode]:
    """未生成の全記事をポッドキャストに変換

    Args:
        output_dir: 音声出力ディレクトリ
        existing_slugs: 既にエピソード化済みの記事スラッグ集合

    Returns:
        生成されたエピソード一覧
    """
    existing = existing_slugs or set()
    articles = await fetch_articles()

    published = [
        a for a in articles
        if a.get("status") == "published" and a.get("slug") not in existing
    ]

    if not published:
        logger.info("新規ポッドキャスト対象記事なし")
        return []

    episodes = []
    for article in published:
        slug = article["slug"]
        try:
            ep = await generate_episode(slug, output_dir)
            episodes.append(ep)
            logger.info("エピソード生成完了: %s", ep.title)
        except Exception:
            logger.exception("エピソード生成失敗: %s", slug)

    return episodes
