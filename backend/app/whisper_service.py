from __future__ import annotations

from pathlib import Path
from threading import Lock

from backend.app.config import settings

_model = None
_lock = Lock()
_import_error: str | None = None


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


def transcribe_file(path: Path, language: str = "ja") -> dict:
    model = get_whisper()
    segments, info = model.transcribe(str(path), language=language)
    text_parts = []
    for seg in segments:
        text_parts.append(seg.text.strip())
    return {
        "text": "".join(text_parts).strip(),
        "language": getattr(info, "language", language),
    }


def whisper_status() -> dict:
    return {
        "ok": _import_error is None,
        "model": settings.whisper_model,
        "device": settings.whisper_device,
        "loaded": _model is not None,
        "error": _import_error,
        "note": "Model loads on first transcription",
    }
