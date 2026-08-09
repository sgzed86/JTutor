from __future__ import annotations

import os
import time
import uuid

from fastapi import APIRouter

from backend.app import ollama_client, voicevox_client
from backend.app.config import settings
from backend.app.speech.stt import transcription_service
from backend.app.speech.tts import speech_service

router = APIRouter()

# Identifies this backend process so the Electron supervisor can tell its own
# child apart from a stray backend left over from a previous run.
INSTANCE_ID = uuid.uuid4().hex
STARTED_AT = time.time()


@router.get("/health")
async def health():
    ollama = await ollama_client.check_ollama()
    vv = await voicevox_client.check_voicevox()
    whisper = transcription_service.status()
    return {
        "ok": True,
        "backend": True,
        "instance_id": INSTANCE_ID,
        "pid": os.getpid(),
        "uptime_s": round(time.time() - STARTED_AT, 1),
        "app": "jtutor",
        "ollama": ollama,
        "voicevox": vv,
        "whisper": whisper,
        "services": {
            "backend": {"ok": True, "required": True},
            "ollama": {"ok": bool(ollama.get("ok")), "required": False},
            "voicevox": {"ok": bool(vv.get("ok")), "required": False},
            "whisper": {"ok": bool(whisper.get("ok")) and whisper.get("state") != "error", "required": False},
        },
        "settings": {
            "ollama_model": settings.ollama_model,
            "selected_speaker_id": voicevox_client.get_selected_speaker_id(),
            "voicevox_speaker": voicevox_client.get_selected_speaker_id(),
            "whisper_model": settings.whisper_model,
            "mastery_min_score": settings.mastery_min_score,
            "log_path": str(settings.log_path),
            "data_dir": str(settings.data_dir),
            "assets_dir": str(settings.assets_dir),
            "tts_cache": speech_service.stats(),
        },
    }
