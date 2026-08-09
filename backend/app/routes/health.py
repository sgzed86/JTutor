from __future__ import annotations

from fastapi import APIRouter

from backend.app import ollama_client, voicevox_client
from backend.app.config import settings
from backend.app.whisper_service import whisper_status

router = APIRouter()


@router.get("/health")
async def health():
    ollama = await ollama_client.check_ollama()
    vv = await voicevox_client.check_voicevox()
    return {
        "ok": True,
        "backend": True,
        "ollama": ollama,
        "voicevox": vv,
        "whisper": whisper_status(),
        "settings": {
            "ollama_model": settings.ollama_model,
            "selected_speaker_id": voicevox_client.get_selected_speaker_id(),
            "voicevox_speaker": voicevox_client.get_selected_speaker_id(),
            "whisper_model": settings.whisper_model,
            "mastery_min_score": settings.mastery_min_score,
            "log_path": str(settings.log_path),
        },
    }
