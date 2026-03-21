from __future__ import annotations

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
        payload = {
            "caption": params.caption,
            "instrumental": params.instrumental,
            "duration": params.duration,
            "num_steps": params.num_steps,
            "cfg_scale": params.cfg_scale,
            "seed": seed,
        }
        if params.lyrics:
            payload["lyrics"] = params.lyrics
        if params.bpm is not None:
            payload["bpm"] = params.bpm
        if params.key:
            payload["key"] = params.key
        if params.time_signature is not None:
            payload["time_signature"] = params.time_signature
        if params.vocal_language:
            payload["vocal_language"] = params.vocal_language

        last_error: Exception | None = None
        for attempt in range(self.retries):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.post(
                        f"{self.base_url}/generate",
                        json=payload,
                    )
                    if response.status_code == 503:
                        last_error = GenerationError(f"Service unavailable (attempt {attempt + 1})")
                        continue
                    response.raise_for_status()
                    return GenerationResult(
                        audio_data=response.content,
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
