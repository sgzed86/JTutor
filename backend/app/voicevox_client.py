from __future__ import annotations

import httpx

from backend.app.config import settings

_selected_speaker_id: int | None = None
_SPEAKER_SETTING_KEY = "selected_speaker_id"
_SPEED_KEY = "voice_speed_scale"
_http_client: httpx.AsyncClient | None = None
_tts_cache: dict[tuple[str, int], bytes] = {}
_TTS_CACHE_MAX = 256


def _default_speaker_id() -> int:
    return int(settings.selected_speaker_id or settings.voicevox_speaker or 2)


def get_selected_speaker_id() -> int:
    global _selected_speaker_id
    if _selected_speaker_id is not None:
        return _selected_speaker_id
    try:
        from backend.app.db import SessionLocal, SettingRow

        with SessionLocal() as db:
            row = db.get(SettingRow, _SPEAKER_SETTING_KEY)
            if row and row.value.strip().isdigit():
                _selected_speaker_id = int(row.value.strip())
                return _selected_speaker_id
    except Exception:
        pass
    _selected_speaker_id = _default_speaker_id()
    return _selected_speaker_id


def get_speed_scale() -> float:
    try:
        from backend.app.db import SessionLocal, SettingRow

        with SessionLocal() as db:
            row = db.get(SettingRow, _SPEED_KEY)
            if row and row.value.strip():
                v = float(row.value.strip())
                return max(0.5, min(2.0, v))
    except Exception:
        pass
    return float(getattr(settings, "voice_speed_scale", 0.95) or 0.95)


def set_selected_speaker_id(speaker_id: int) -> int:
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
    except Exception:
        pass
    return _selected_speaker_id


async def _client() -> httpx.AsyncClient:
    global _http_client
    if _http_client is None:
        _http_client = httpx.AsyncClient(timeout=60.0)
    return _http_client


async def check_voicevox() -> dict:
    try:
        client = await _client()
        r = await client.get(f"{settings.voicevox_url}/version")
        if r.status_code >= 400:
            r = await client.get(f"{settings.voicevox_url}/docs")
        return {"ok": r.status_code < 500, "status": r.status_code}
    except Exception as e:
        return {"ok": False, "error": str(e)}


async def list_speakers() -> list[dict]:
    client = await _client()
    r = await client.get(f"{settings.voicevox_url}/speakers")
    r.raise_for_status()
    data = r.json()
    return data if isinstance(data, list) else []


def prepare_for_voicevox(text: str) -> str:
    import re

    t = (text or "").strip()
    t = re.sub(r"```[\s\S]*?```", " ", t)
    t = re.sub(r"[*_`#]+", " ", t)
    t = re.sub(r"\([A-Za-z][^)]{0,80}\)", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    if re.search(r"[\u3040-\u30ff\u4e00-\u9fff]", t):
        t = re.sub(r"[A-Za-z]{3,}", " ", t)
        t = re.sub(r"\s+", " ", t).strip()
    return t[:300]


async def synthesize(text: str, speaker: int | None = None) -> bytes:
    speaker = speaker if speaker is not None else get_selected_speaker_id()
    text = prepare_for_voicevox(text)
    if not text:
        raise ValueError("Nothing speakable for VoiceVox")
    cache_key = (text, speaker)
    if cache_key in _tts_cache:
        return _tts_cache[cache_key]

    client = await _client()
    q = await client.post(
        f"{settings.voicevox_url}/audio_query",
        params={"text": text, "speaker": speaker},
    )
    q.raise_for_status()
    query = q.json()
    query["speedScale"] = get_speed_scale()
    s = await client.post(
        f"{settings.voicevox_url}/synthesis",
        params={"speaker": speaker},
        json=query,
    )
    s.raise_for_status()
    wav = s.content
    if len(_tts_cache) >= _TTS_CACHE_MAX:
        _tts_cache.pop(next(iter(_tts_cache)))
    _tts_cache[cache_key] = wav
    return wav
