from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel

from backend.app import user_settings
from backend.app.logging_setup import log_event

router = APIRouter()


class PatchIn(BaseModel):
    voice: dict[str, Any] | None = None
    audio: dict[str, Any] | None = None
    appearance: dict[str, Any] | None = None
    lessons: dict[str, Any] | None = None
    ask_yuki: dict[str, Any] | None = None
    advanced: dict[str, Any] | None = None


@router.get("")
def get_settings() -> user_settings.UserSettings:
    return user_settings.load()


@router.patch("")
def patch_settings(body: PatchIn) -> user_settings.UserSettings:
    changes = dict(body.model_dump(exclude_none=True))
    updated = user_settings.patch(changes)
    log_event("settings", "patched", sections=sorted(changes.keys()))
    return updated


@router.post("/reset")
def reset_settings() -> user_settings.UserSettings:
    log_event("settings", "reset")
    return user_settings.reset()
