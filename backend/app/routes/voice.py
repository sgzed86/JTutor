from __future__ import annotations

import tempfile
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import Response
from pydantic import BaseModel, Field

from backend.app import voicevox_client
from backend.app.config import settings
from backend.app.logging_setup import log_event
from backend.app.whisper_service import transcribe_file

router = APIRouter()


class SpeakIn(BaseModel):
    text: str
    speaker_id: int | None = None


class SetSpeakerIn(BaseModel):
    speaker_id: int = Field(..., ge=0)


class SetSpeedIn(BaseModel):
    speed_scale: float = Field(..., ge=0.5, le=2.0)


@router.post("/speak")
async def speak(body: SpeakIn):
    if not body.text.strip():
        raise HTTPException(400, "Empty text")
    try:
        wav = await voicevox_client.synthesize(body.text, body.speaker_id)
    except Exception as e:
        log_event("voice", "speak_error", error=str(e), chars=len(body.text))
        raise HTTPException(503, f"VoiceVox error: {e}")
    log_event(
        "voice",
        "speak",
        chars=len(body.text),
        speaker_id=body.speaker_id if body.speaker_id is not None else voicevox_client.get_selected_speaker_id(),
    )
    return Response(content=wav, media_type="audio/wav")


@router.get("/speakers")
async def speakers():
    """List VoiceVox characters and styles (proxied from the engine)."""
    try:
        raw = await voicevox_client.list_speakers()
    except Exception as e:
        log_event("voice", "speakers_error", error=str(e)[:200])
        raise HTTPException(503, f"VoiceVox speakers unavailable: {e}")
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
    log_event("voice", "set_speaker", speaker_id=sid)
    return {"ok": True, "selected_speaker_id": sid}


@router.post("/set-speed")
def set_speed(body: SetSpeedIn):
    scale = voicevox_client.set_speed_scale(body.speed_scale)
    log_event("voice", "set_speed", speed_scale=scale)
    return {"ok": True, "voice_speed_scale": scale}


@router.post("/transcribe")
def transcribe(file: UploadFile = File(...)):
    suffix = Path(file.filename or "audio.webm").suffix or ".webm"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        data = file.file.read()
        tmp.write(data)
        tmp_path = Path(tmp.name)
    try:
        result = transcribe_file(tmp_path, language="ja")
    except Exception as e:
        log_event("voice", "transcribe_error", error=str(e), bytes=len(data))
        raise HTTPException(500, f"Whisper error: {e}")
    finally:
        tmp_path.unlink(missing_ok=True)
    log_event(
        "voice",
        "transcribe",
        bytes=len(data),
        text=(result.get("text") or "")[:200],
    )
    return result


@router.get("/settings")
def voice_settings():
    return {
        "selected_speaker_id": voicevox_client.get_selected_speaker_id(),
        "voicevox_speaker": voicevox_client.get_selected_speaker_id(),  # legacy alias
        "default_speaker_id": settings.selected_speaker_id,
        "whisper_model": settings.whisper_model,
        "whisper_device": settings.whisper_device,
        "voice_speed_scale": voicevox_client.get_speed_scale(),
    }
