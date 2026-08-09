"""Typed tutor step contract (Tier 3.3)."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class TutorStep(BaseModel):
    model_config = ConfigDict(extra="allow")

    phase: str | None = None
    book_mode: str | None = None
    book_substep: str | None = None
    expect_speech: bool = False
    auto_advance_after_audio: bool = False
    play_audio: list[str] = Field(default_factory=list)
    instruction_en: str | None = None
    say_target_jp: str | None = None
    help: bool = False


def coerce_step(step: dict | None) -> dict:
    if not step:
        return {}
    try:
        return TutorStep.model_validate(step).model_dump(exclude_none=False)
    except Exception:
        return dict(step)
