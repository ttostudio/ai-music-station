from __future__ import annotations

import base64
import json
import random
from dataclasses import dataclass

import httpx

from worker.config import settings


class GenerationError(Exception):
    pass


class GenerationTimeoutError(GenerationError):
    pass


@dataclass
class GenerationParams:
    caption: str
    lyrics: str | None = None
    instrumental: bool = True
    bpm: int | None = None
    duration: int = 180
    key: str | None = None
    time_signature: int | None = 4
    vocal_language: str | None = None
    num_steps: int = 8
    cfg_scale: float = 7.0
    seed: int | None = None


@dataclass
class GenerationResult:
    audio_data: bytes
    sample_rate: int
    seed: int
    duration_ms: int


def _build_prompt(params: GenerationParams) -> str:
    """Build a natural language prompt for ACE-Step from generation params."""
    parts = [params.caption]
    if params.bpm is not None:
        parts.append(f"BPM: {params.bpm}")
    if params.key:
        parts.append(f"Key: {params.key}")
    if params.instrumental:
        parts.append("Instrumental")
    if params.lyrics:
        parts.append(f"Lyrics: {params.lyrics}")
    if params.duration:
        parts.append(f"Duration: {params.duration}s")
    return ". ".join(parts)


class ACEStepClient:
    def __init__(
        self,
        base_url: str = settings.acestep_api_url,
        timeout: int = settings.acestep_timeout,
        retries: int = settings.acestep_retries,
    ):
        self.base_url = base_url
        self.timeout = timeout
        self.retries = retries

    async def generate(self, params: GenerationParams) -> GenerationResult:
        seed = params.seed if params.seed is not None else random.randint(0, 2**31 - 1)

        # OpenRouter-compatible chat completions format
        payload = {
            "model": "ace-step-v1.5",
            "messages": [
                {
                    "role": "user",
                    "content": _build_prompt(params),
                }
            ],
            "stream": False,
        }

        last_error: Exception | None = None
        for attempt in range(self.retries):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.post(
                        f"{self.base_url}/v1/chat/completions",
                        json=payload,
                    )
                    if response.status_code == 503:
                        last_error = GenerationError(f"Service unavailable (attempt {attempt + 1})")
                        continue
                    response.raise_for_status()

                    data = response.json()
                    audio_data = self._extract_audio(data)
                    return GenerationResult(
                        audio_data=audio_data,
                        sample_rate=48000,
                        seed=seed,
                        duration_ms=params.duration * 1000,
                    )
            except httpx.TimeoutException as e:
                raise GenerationTimeoutError(f"Generation timed out after {self.timeout}s") from e
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 503:
                    last_error = e
                    continue
                raise GenerationError(
                    f"ACE-Step API error: {e.response.status_code} {e.response.text}"
                ) from e
            except httpx.RequestError as e:
                last_error = GenerationError(f"Connection error: {e}")
                last_error.__cause__ = e
                continue

        raise last_error or GenerationError("Generation failed after retries")

    def _extract_audio(self, data: dict) -> bytes:
        """Extract audio bytes from chat completions response.

        ACE-Step returns audio as base64-encoded data in the response content,
        or as a URL pointing to the generated audio file.
        """
        try:
            choices = data.get("choices", [])
            if not choices:
                raise GenerationError("No choices in response")

            content = choices[0].get("message", {}).get("content", "")

            # Try parsing content as JSON (may contain audio_url or audio_base64)
            try:
                content_data = json.loads(content) if isinstance(content, str) else content
                if isinstance(content_data, dict):
                    # Base64 encoded audio
                    if "audio_base64" in content_data:
                        return base64.b64decode(content_data["audio_base64"])
                    # Audio URL - download it
                    if "audio_url" in content_data:
                        return self._download_audio(content_data["audio_url"])
            except (json.JSONDecodeError, TypeError):
                pass

            # Content might be base64 audio directly
            if content and len(content) > 1000:
                try:
                    return base64.b64decode(content)
                except Exception:
                    pass

            # Check for audio in the response metadata
            if "audio" in data:
                audio = data["audio"]
                if isinstance(audio, str):
                    return base64.b64decode(audio)
                if isinstance(audio, dict) and "data" in audio:
                    return base64.b64decode(audio["data"])

            raise GenerationError(f"Could not extract audio from response: {list(data.keys())}")

        except GenerationError:
            raise
        except Exception as e:
            raise GenerationError(f"Failed to parse generation response: {e}") from e

    def _download_audio(self, url: str) -> bytes:
        """Download audio from a URL synchronously (called within async context)."""
        import httpx as _httpx
        with _httpx.Client(timeout=30) as client:
            resp = client.get(url)
            resp.raise_for_status()
            return resp.content
