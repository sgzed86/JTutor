"""Whisper transcription on a dedicated worker thread.

`faster-whisper` is synchronous and CPU-bound. Calling it directly from an
`async def` route blocks the whole event loop for the duration of the
transcription — including `/health` — which made the app look hung. A single
worker thread keeps the loop free and serialises model use.
"""

from __future__ import annotations

import asyncio
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path
from threading import Lock

from backend.app.config import settings
from backend.app.logging_setup import get_logger, log_event

_log = get_logger("speech.stt")


class WhisperUnavailable(RuntimeError):
    """The speech model could not be loaded."""


@dataclass
class Transcript:
    text: str
    language: str
    duration_s: float = 0.0
    avg_logprob: float | None = None
    no_speech_prob: float | None = None
    segments: list[dict] = field(default_factory=list)

    def as_dict(self) -> dict:
        return {
            "text": self.text,
            "language": self.language,
            "duration_s": round(self.duration_s, 3),
            "avg_logprob": self.avg_logprob,
            "no_speech_prob": self.no_speech_prob,
        }


class TranscriptionService:
    """Loads the model once, off the event loop, and serialises transcriptions."""

    def __init__(self) -> None:
        self._pool = ThreadPoolExecutor(max_workers=1, thread_name_prefix="whisper")
        self._model = None
        self._state = "idle"  # idle | loading | ready | error
        self._error: str | None = None
        self._lock = Lock()
        self._loaded_at: float | None = None

    # ---- lifecycle -------------------------------------------------------
    def _load_sync(self) -> None:
        with self._lock:
            if self._model is not None:
                return
            self._state = "loading"
        try:
            from faster_whisper import WhisperModel

            compute = "int8" if settings.whisper_device == "cpu" else "float16"
            started = time.perf_counter()
            model = WhisperModel(
                settings.whisper_model,
                device=settings.whisper_device,
                compute_type=compute,
            )
        except Exception as exc:  # noqa: BLE001 - surfaced through status()
            with self._lock:
                self._state = "error"
                self._error = str(exc)
            _log.warning("whisper load failed: %s", exc)
            raise WhisperUnavailable(str(exc)) from exc
        with self._lock:
            self._model = model
            self._state = "ready"
            self._error = None
            self._loaded_at = time.time()
        log_event(
            "speech.stt",
            "model_ready",
            model=settings.whisper_model,
            device=settings.whisper_device,
            ms=int((time.perf_counter() - started) * 1000),
        )

    async def warm(self) -> None:
        """Load the model in the background so the first recording is fast."""
        if self._state in ("ready", "loading"):
            return
        loop = asyncio.get_running_loop()
        try:
            await loop.run_in_executor(self._pool, self._load_sync)
        except WhisperUnavailable:
            pass  # status() reports it; the app still runs without STT

    def status(self) -> dict:
        return {
            "ok": self._state != "error",
            "state": self._state,
            "loaded": self._model is not None,
            "model": settings.whisper_model,
            "device": settings.whisper_device,
            "error": self._error,
            "loaded_at": self._loaded_at,
        }

    # ---- transcription ---------------------------------------------------
    def _transcribe_sync(self, path: Path, language: str | None) -> Transcript:
        self._load_sync()
        assert self._model is not None
        segments, info = self._model.transcribe(str(path), language=language)
        parts: list[str] = []
        raw: list[dict] = []
        logprobs: list[float] = []
        no_speech: list[float] = []
        for seg in segments:
            parts.append((seg.text or "").strip())
            raw.append({"start": seg.start, "end": seg.end, "text": seg.text})
            if getattr(seg, "avg_logprob", None) is not None:
                logprobs.append(seg.avg_logprob)
            if getattr(seg, "no_speech_prob", None) is not None:
                no_speech.append(seg.no_speech_prob)
        return Transcript(
            text="".join(parts).strip(),
            language=getattr(info, "language", language or "ja"),
            duration_s=float(getattr(info, "duration", 0.0) or 0.0),
            avg_logprob=(sum(logprobs) / len(logprobs)) if logprobs else None,
            no_speech_prob=(max(no_speech) if no_speech else None),
        )

    async def transcribe(self, path: Path, *, language: str | None = "ja") -> Transcript:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(self._pool, self._transcribe_sync, path, language)

    def shutdown(self) -> None:
        self._pool.shutdown(wait=False, cancel_futures=True)


transcription_service = TranscriptionService()
