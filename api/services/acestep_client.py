"""ACE-Step REST API クライアント（正式実装）。

接続先: ACESTEP_API_URL 環境変数（デフォルト: http://host.docker.internal:8001）
"""
from __future__ import annotations

import logging
import re
import urllib.parse
from dataclasses import dataclass
from pathlib import Path

import httpx

logger = logging.getLogger(__name__)

VOCAL_LANGUAGE_ALLOWLIST = frozenset(
    {"ja", "en", "ko", "zh", "fr", "es", "de", "pt", "it", "ru"}
)

_MUSIC_KEY_RE = re.compile(r"^[A-Ga-g#b♭ ]{0,10}$")
_CONTROL_CHARS_RE = re.compile(r"[\x00-\x08\x0b-\x1f]")


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------


class AceStepError(Exception):
    """ACE-Step API 呼び出しの汎用エラー。"""


class AceStepTimeoutError(AceStepError):
    """生成タイムアウト。"""


class AceStepQueueFullError(AceStepError):
    """ACE-Step のキューが満杯（HTTP 429）。"""


# ---------------------------------------------------------------------------
# Result dataclass
# ---------------------------------------------------------------------------


@dataclass
class AceStepJobResult:
    """POST /query_result の 1 ジョブ分レスポンス。

    status は内部統一ステータス: pending | processing | completed | failed
    （ACE-Step の "success" は "completed" にマッピング済み）
    """

    status: str
    audio_path: str | None = None
    duration: float | None = None
    bpm: int | None = None
    key_scale: str | None = None
    lyrics: str | None = None
    error: str | None = None


# ---------------------------------------------------------------------------
# Input sanitizers
# ---------------------------------------------------------------------------


def sanitize_prompt(value: str) -> str:
    """制御文字を除去し、最大 1000 文字にクリップ。"""
    return _CONTROL_CHARS_RE.sub("", value)[:1000]


def sanitize_lyrics(value: str) -> str:
    """制御文字を除去し、最大 5000 文字にクリップ。"""
    return _CONTROL_CHARS_RE.sub("", value)[:5000]


def sanitize_bpm(value: int | None) -> int | None:
    """30–300 にクランプ。"""
    if value is None:
        return None
    return max(30, min(300, int(value)))


def sanitize_duration(value: float | int | None) -> float | None:
    """10–600 にクランプ。"""
    if value is None:
        return None
    return max(10.0, min(600.0, float(value)))


def sanitize_music_key(value: str | None) -> str | None:
    """許可文字のみ、最大 10 文字。不正な場合は None を返す。"""
    if not value:
        return None
    cleaned = value[:10]
    if _MUSIC_KEY_RE.match(cleaned):
        return cleaned
    return None


def sanitize_vocal_language(value: str | None) -> str:
    """allowlist 以外は "ja" にフォールバック。"""
    if value and value in VOCAL_LANGUAGE_ALLOWLIST:
        return value
    return "ja"


# ---------------------------------------------------------------------------
# Client
# ---------------------------------------------------------------------------


class AceStepClient:
    """ACE-Step REST API クライアント。

    Args:
        base_url: ACE-Step サーバーの URL（末尾スラッシュ不要）。
        timeout: デフォルトの HTTP タイムアウト（秒）。
    """

    def __init__(self, base_url: str, timeout: float = 30.0) -> None:
        self._base_url = base_url.rstrip("/")
        self._client = httpx.AsyncClient(timeout=timeout)

    async def aclose(self) -> None:
        await self._client.aclose()

    async def health_check(self) -> bool:
        """GET /health を確認する。タイムアウト 5 秒。"""
        try:
            resp = await self._client.get(
                f"{self._base_url}/health", timeout=5.0
            )
            return resp.status_code == 200
        except Exception:
            return False

    async def submit_job(self, params: dict) -> str:
        """POST /release_task でジョブを投入し、task_id を返す。

        Raises:
            AceStepQueueFullError: HTTP 429 またはキュー満杯エラー。
            AceStepError: その他の API エラー。
        """
        try:
            resp = await self._client.post(
                f"{self._base_url}/release_task", json=params
            )
        except httpx.ConnectError as exc:
            raise AceStepError(f"ACE-Step 接続失敗: {exc}") from exc
        except httpx.TimeoutException as exc:
            raise AceStepError(f"ACE-Step タイムアウト: {exc}") from exc

        if resp.status_code == 429:
            raise AceStepQueueFullError("ACE-Step キューが満杯です")
        resp.raise_for_status()

        data = resp.json()
        if data.get("code") != 200:
            raise AceStepError(f"ACE-Step エラー: {data.get('error')}")
        return data["data"]["task_id"]

    async def poll_result(self, job_id: str) -> AceStepJobResult:
        """POST /query_result でジョブのステータスを取得する。

        Raises:
            AceStepError: 接続エラーまたはタイムアウト。
        """
        try:
            resp = await self._client.post(
                f"{self._base_url}/query_result",
                json={"task_ids": [job_id]},
            )
        except httpx.ConnectError as exc:
            raise AceStepError(f"ACE-Step 接続失敗: {exc}") from exc
        except httpx.TimeoutException as exc:
            raise AceStepError(f"ACE-Step タイムアウト: {exc}") from exc

        resp.raise_for_status()
        data = resp.json()
        # data["data"] は list（完了したジョブの配列）または空リスト
        results = data.get("data", [])
        if isinstance(results, list) and len(results) > 0:
            # リストの中から該当ジョブを探す
            job_data = next((r for r in results if r.get("task_id") == job_id), {})
        elif isinstance(results, dict):
            job_data = results.get(job_id, {})
        else:
            job_data = {}
        raw_status = job_data.get("status", "pending")

        # ACE-Step の "success" を内部統一ステータス "completed" にマッピング
        status = "completed" if raw_status == "success" else raw_status

        return AceStepJobResult(
            status=status,
            audio_path=job_data.get("audio_path"),
            duration=job_data.get("duration"),
            bpm=job_data.get("bpm"),
            key_scale=job_data.get("key_scale"),
            lyrics=job_data.get("lyrics"),
            error=job_data.get("error"),
        )

    async def download_audio(self, audio_path: str, dest_path: Path) -> int:
        """GET /v1/audio?path=... でファイルをダウンロードし、dest_path に保存。

        Args:
            audio_path: ACE-Step が返したローカルパス文字列。
            dest_path: 保存先 Path オブジェクト。

        Returns:
            保存したファイルサイズ（バイト）。

        Raises:
            AceStepError: ダウンロード失敗。
        """
        encoded_path = urllib.parse.quote(audio_path, safe="")
        url = f"{self._base_url}/v1/audio?path={encoded_path}"
        try:
            resp = await self._client.get(url, timeout=120.0)
        except httpx.TimeoutException as exc:
            raise AceStepError(f"音声ダウンロードタイムアウト: {exc}") from exc
        except httpx.ConnectError as exc:
            raise AceStepError(f"音声ダウンロード接続失敗: {exc}") from exc

        resp.raise_for_status()
        dest_path.write_bytes(resp.content)
        return len(resp.content)
