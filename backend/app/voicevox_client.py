"""VOICEVOX engine client: reachability, speaker catalogue and speaker selection.

Synthesis itself lives in `backend.app.speech.tts` so it can be cached.
"""

from __future__ import annotations

import httpx

from backend.app.config import settings
from backend.app.logging_setup import get_logger
from backend.app.speech.text import prepare_for_voicevox  # re-exported for callers
from backend.app.speech.tts import SynthesisRequest, VoicevoxUnavailable, speech_service

_log = get_logger("voicevox")

# In-process selection; seeded from config / DB on first read.
_selected_speaker_id: int | None = None
_SPEAKER_SETTING_KEY = "selected_speaker_id"

__all__ = [
    "VoicevoxUnavailable",
    "check_voicevox",
    "get_selected_speaker_id",
    "list_speakers",
    "prepare_for_voicevox",
    "set_selected_speaker_id",
    "synthesize",
]


def _default_speaker_id() -> int:
    # Prefer selected_speaker_id; fall back to legacy VOICEVOX_SPEAKER.
    return int(settings.selected_speaker_id or settings.voicevox_speaker or 2)


def get_selected_speaker_id() -> int:
    global _selected_speaker_id
    if _selected_speaker_id is not None:
        return _selected_speaker_id
    # Lazy-load persisted choice from SQLite when available.
    try:
        from backend.app.db import SessionLocal, SettingRow

        with SessionLocal() as db:
            row = db.get(SettingRow, _SPEAKER_SETTING_KEY)
            if row and row.value.strip().isdigit():
                _selected_speaker_id = int(row.value.strip())
                return _selected_speaker_id
    except Exception as exc:  # noqa: BLE001 - config read must not break synthesis
        _log.warning("could not read persisted speaker id: %s", exc)
    _selected_speaker_id = _default_speaker_id()
    return _selected_speaker_id


def set_selected_speaker_id(speaker_id: int) -> int:
    """Update runtime + persist speaker style id used for all synthesis."""
    global _selected_speaker_id
    speaker_id = int(speaker_id)
    _selected_speaker_id = speaker_id
    try:
        from backend.app.db import SessionLocal, SettingRow

        with SessionLocal() as db:
            row = db.get(SettingRow, _SPEAKER_SETTING_KEY)
            if row is None:
                db.add(SettingRow(key=_SPEAKER_SETTING_KEY, value=str(speaker_id)))
            else:
                row.value = str(speaker_id)
            db.commit()
    except Exception as exc:  # noqa: BLE001 - selection still applies in-process
        _log.warning("could not persist speaker id %s: %s", speaker_id, exc)
    return _selected_speaker_id


async def check_voicevox() -> dict:
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            r = await client.get(f"{settings.voicevox_url}/version")
            if r.status_code >= 400:
                r = await client.get(f"{settings.voicevox_url}/docs")
            return {"ok": r.status_code < 500, "status": r.status_code}
    except Exception as e:  # noqa: BLE001 - health probe reports, never raises
        return {"ok": False, "error": str(e)}


async def list_speakers() -> list[dict]:
    """Proxy VOICEVOX GET /speakers (character + style list)."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.get(f"{settings.voicevox_url}/speakers")
            r.raise_for_status()
            data = r.json()
            return data if isinstance(data, list) else []
    except httpx.HTTPError as exc:
        raise VoicevoxUnavailable(str(exc)) from exc


async def synthesize(
    text: str,
    speaker: int | None = None,
    *,
    speed: float = 1.0,
    pitch: float = 0.0,
) -> bytes:
    speaker = speaker if speaker is not None else get_selected_speaker_id()
    return await speech_service.synthesize(
        SynthesisRequest(text=text, speaker=int(speaker), speed=speed, pitch=pitch)
    )
