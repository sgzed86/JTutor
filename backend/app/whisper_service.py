from __future__ import annotations

from pathlib import Path
from threading import Lock

from backend.app.config import settings

_model = None
_lock = Lock()
_job_lock = Lock()
_import_error: str | None = None
_warm_attempted = False


def get_whisper():
    global _model, _import_error
    with _lock:
        if _model is None:
            try:
                from faster_whisper import WhisperModel
            except Exception as e:
                _import_error = str(e)
                raise
            _model = WhisperModel(
                settings.whisper_model,
                device=settings.whisper_device,
                compute_type="int8" if settings.whisper_device == "cpu" else "float16",
            )
        return _model


def warm_whisper() -> None:
    """Load model in a background-friendly call (startup thread)."""
    global _warm_attempted, _import_error
    if _warm_attempted:
        return
    _warm_attempted = True
    try:
        get_whisper()
    except Exception as e:
        _import_error = str(e)


def transcribe_file(path: Path, language: str = "ja", *, prompt: str | None = None) -> dict:
    """Serialize decode jobs (Tier 3.5 — single worker lock)."""
    with _job_lock:
        return _transcribe_inner(path, language, prompt=prompt)


def _transcribe_inner(path: Path, language: str, *, prompt: str | None) -> dict:
    model = get_whisper()
    kwargs: dict = {
        "language": language,
        "beam_size": 1,
        "vad_filter": True,
        "condition_on_previous_text": False,
        "without_timestamps": True,
    }
    if prompt:
        kwargs["initial_prompt"] = prompt[:200]
    segments, info = model.transcribe(str(path), **kwargs)
    text_parts = []
    for seg in segments:
        text_parts.append(seg.text.strip())
    text = "".join(text_parts).strip()
    return {
        "text": text,
        "language": getattr(info, "language", language),
    }


def whisper_status() -> dict:
    installed = _import_error is None or _model is not None
    if _import_error and _model is None:
        installed = False
    return {
        "ok": installed,
        "model": settings.whisper_model,
        "device": settings.whisper_device,
        "loaded": _model is not None,
        "error": _import_error,
        "note": "Model loads on first transcription unless warmed at startup",
    }
