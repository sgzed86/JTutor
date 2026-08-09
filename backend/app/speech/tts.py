"""VOICEVOX synthesis with an on-disk cache.

Tutor lines are highly repetitive (`よくできました。` fires on nearly every graded
step) and each synthesis costs two HTTP round-trips to the engine. Caching by
(text, speaker, speed, pitch) removes almost all of that latency.
"""

from __future__ import annotations

import asyncio
import hashlib
import time
from dataclasses import dataclass
from pathlib import Path

import httpx

from backend.app.config import settings
from backend.app.logging_setup import get_logger, log_event
from backend.app.speech.text import prepare_for_voicevox

_log = get_logger("speech.tts")

# Bound the cache so a long-running install cannot fill the disk.
MAX_CACHE_BYTES = 256 * 1024 * 1024


class VoicevoxUnavailable(RuntimeError):
    """The engine could not be reached or refused the request."""


@dataclass(frozen=True)
class SynthesisRequest:
    text: str
    speaker: int
    speed: float = 1.0
    pitch: float = 0.0
    intonation: float = 1.0

    def cache_key(self) -> str:
        raw = f"{self.text}|{self.speaker}|{self.speed:.2f}|{self.pitch:.2f}|{self.intonation:.2f}"
        return hashlib.sha1(raw.encode("utf-8")).hexdigest()


class SpeechService:
    def __init__(self) -> None:
        self._locks: dict[str, asyncio.Lock] = {}
        self._hits = 0
        self._misses = 0

    # ---- cache -----------------------------------------------------------
    def _cache_file(self, key: str) -> Path:
        return settings.tts_cache_dir / f"{key}.wav"

    def _read_cache(self, key: str) -> bytes | None:
        path = self._cache_file(key)
        try:
            data = path.read_bytes()
        except OSError:
            return None
        # Touch so the LRU sweep keeps frequently used lines.
        try:
            path.touch()
        except OSError:
            pass
        return data or None

    def _write_cache(self, key: str, data: bytes) -> None:
        path = self._cache_file(key)
        tmp = path.with_suffix(".part")
        try:
            tmp.write_bytes(data)
            tmp.replace(path)
        except OSError as exc:
            _log.warning("tts cache write failed: %s", exc)

    def sweep_cache(self, max_bytes: int = MAX_CACHE_BYTES) -> int:
        """Drop least-recently-used entries until the cache fits. Returns bytes freed."""
        try:
            files = sorted(
                (p for p in settings.tts_cache_dir.glob("*.wav")),
                key=lambda p: p.stat().st_mtime,
            )
        except OSError:
            return 0
        total = sum(p.stat().st_size for p in files)
        freed = 0
        for path in files:
            if total - freed <= max_bytes:
                break
            try:
                size = path.stat().st_size
                path.unlink()
                freed += size
            except OSError:
                continue
        if freed:
            _log.info("tts cache swept freed=%s bytes", freed)
        return freed

    def stats(self) -> dict:
        try:
            files = list(settings.tts_cache_dir.glob("*.wav"))
            size = sum(p.stat().st_size for p in files)
        except OSError:
            files, size = [], 0
        return {
            "entries": len(files),
            "bytes": size,
            "hits": self._hits,
            "misses": self._misses,
        }

    # ---- synthesis -------------------------------------------------------
    async def synthesize(self, req: SynthesisRequest) -> bytes:
        text = prepare_for_voicevox(req.text)
        if not text:
            raise ValueError("Nothing speakable for VOICEVOX")
        req = SynthesisRequest(text, req.speaker, req.speed, req.pitch, req.intonation)
        key = req.cache_key()

        cached = self._read_cache(key)
        if cached is not None:
            self._hits += 1
            return cached

        lock = self._locks.setdefault(key, asyncio.Lock())
        async with lock:
            cached = self._read_cache(key)
            if cached is not None:
                self._hits += 1
                return cached
            self._misses += 1
            started = time.perf_counter()
            data = await self._synthesize_remote(req)
            self._write_cache(key, data)
            log_event(
                "speech.tts",
                "synthesized",
                chars=len(req.text),
                speaker=req.speaker,
                ms=int((time.perf_counter() - started) * 1000),
            )
        self._locks.pop(key, None)
        return data

    async def _synthesize_remote(self, req: SynthesisRequest) -> bytes:
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                query = await client.post(
                    f"{settings.voicevox_url}/audio_query",
                    params={"text": req.text, "speaker": req.speaker},
                )
                query.raise_for_status()
                payload = query.json()
                payload["speedScale"] = float(req.speed)
                payload["pitchScale"] = float(req.pitch)
                payload["intonationScale"] = float(req.intonation)
                synth = await client.post(
                    f"{settings.voicevox_url}/synthesis",
                    params={"speaker": req.speaker},
                    json=payload,
                )
                synth.raise_for_status()
                return synth.content
        except httpx.HTTPError as exc:
            raise VoicevoxUnavailable(str(exc)) from exc

    async def prewarm(self, lines: list[str], speaker: int) -> int:
        """Synthesise scripted lines into the cache. Best effort, never raises."""
        done = 0
        for line in lines:
            try:
                await self.synthesize(SynthesisRequest(line, speaker))
                done += 1
            except Exception:  # noqa: BLE001 - prewarm must never break startup
                break
        return done


speech_service = SpeechService()
