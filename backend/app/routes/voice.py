from __future__ import annotations

import tempfile
from pathlib import Path

from fastapi import APIRouter, File, Form, UploadFile
from fastapi.responses import Response
from pydantic import BaseModel, Field

from backend.app import user_settings, voicevox_client
from backend.app.config import settings
from backend.app.errors import InvalidRequest, VoicevoxDown, WhisperDown
from backend.app.logging_setup import log_event
from backend.app.speech.stt import transcription_service
from backend.app.speech.tts import VoicevoxUnavailable, speech_service

router = APIRouter()


class SpeakIn(BaseModel):
    text: str
    speaker_id: int | None = None
    speed: float | None = Field(default=None, ge=0.5, le=2.0)
    pitch: float | None = Field(default=None, ge=-0.15, le=0.15)


class SetSpeakerIn(BaseModel):
    speaker_id: int = Field(..., ge=0)


class SetSpeedIn(BaseModel):
    speed_scale: float = Field(..., ge=0.5, le=2.0)


@router.post("/speak")
async def speak(body: SpeakIn):
    if not body.text.strip():
        raise InvalidRequest("Nothing to say.")
    voice = user_settings.load().voice
    try:
        wav = await voicevox_client.synthesize(
            body.text,
            body.speaker_id,
            speed=body.speed if body.speed is not None else voice.speed,
            pitch=body.pitch if body.pitch is not None else voice.pitch,
        )
    except VoicevoxUnavailable as e:
        log_event("voice", "speak_error", error=str(e), chars=len(body.text))
        raise VoicevoxDown(detail=str(e)) from e
    except ValueError as e:
        raise InvalidRequest(str(e)) from e
    log_event(
        "voice",
        "speak",
        chars=len(body.text),
        speaker_id=body.speaker_id if body.speaker_id is not None else voicevox_client.get_selected_speaker_id(),
    )
    return Response(content=wav, media_type="audio/wav")


@router.get("/speakers")
async def speakers():
    """List VOICEVOX characters and styles (proxied from the engine)."""
    try:
        raw = await voicevox_client.list_speakers()
    except VoicevoxUnavailable as e:
        log_event("voice", "speakers_error", error=str(e)[:200])
        raise VoicevoxDown(detail=str(e)) from e
    selected = voicevox_client.get_selected_speaker_id()
    options: list[dict] = []
    for sp in raw:
        name = sp.get("name") or "Speaker"
        for style in sp.get("styles") or []:
            sid = style.get("id")
            if sid is None:
                continue
            options.append(
                {
                    "speaker_id": int(sid),
                    "name": name,
                    "style_name": style.get("name") or "ノーマル",
                    "style_type": style.get("type") or "talk",
                    "label": f"{name} — {style.get('name') or 'ノーマル'} ({sid})",
                }
            )
    return {
        "selected_speaker_id": selected,
        "speakers": raw,
        "options": options,
    }


@router.post("/set-speaker")
async def set_speaker(body: SetSpeakerIn):
    sid = voicevox_client.set_selected_speaker_id(body.speaker_id)
    current = user_settings.load()
    current.voice.speaker_id = sid
    user_settings.save(current)
    log_event("voice", "set_speaker", speaker_id=sid)
    return {"ok": True, "selected_speaker_id": sid}


@router.post("/set-speed")
def set_speed(body: SetSpeedIn):
    scale = voicevox_client.set_speed_scale(body.speed_scale)
    log_event("voice", "set_speed", speed_scale=scale)
    return {"ok": True, "voice_speed_scale": scale}


@router.post("/transcribe")
async def transcribe(
    file: UploadFile = File(...),  # noqa: B008 - FastAPI dependency marker
    language: str = Form("ja"),
):
    suffix = Path(file.filename or "audio.webm").suffix or ".webm"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        data = file.file.read()
        tmp.write(data)
        tmp_path = Path(tmp.name)
    try:
        result = await transcription_service.transcribe(
            tmp_path, language=None if language in ("", "auto") else language
        )
    except Exception as e:  # noqa: BLE001 - reported as a typed problem envelope
        log_event("voice", "transcribe_error", error=str(e), bytes=len(data))
        raise WhisperDown(detail=str(e)) from e
    finally:
        tmp_path.unlink(missing_ok=True)
    log_event(
        "voice",
        "transcribe",
        bytes=len(data),
        text=(result.text or "")[:200],
    )
    return result.as_dict()


@router.get("/model-status")
def model_status():
    """Speech-model readiness, so the UI can say 'preparing' instead of hanging."""
    return transcription_service.status()


@router.post("/warm")
async def warm_model():
    await transcription_service.warm()
    return transcription_service.status()


@router.get("/settings")
def voice_settings():
    return {
        "selected_speaker_id": voicevox_client.get_selected_speaker_id(),
        "voicevox_speaker": voicevox_client.get_selected_speaker_id(),  # legacy alias
        "default_speaker_id": settings.selected_speaker_id,
        "whisper_model": settings.whisper_model,
        "whisper_device": settings.whisper_device,
        "tts_cache": speech_service.stats(),
        "voice_speed_scale": voicevox_client.get_speed_scale(),
    }
