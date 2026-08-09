"""Canonical curriculum models (Tier 3.6)."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ActivityModel(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: str
    kind: str = "activity"
    book_activity: int | None = None
    key_phrases: list[str] = Field(default_factory=list)


class LessonFile(BaseModel):
    model_config = ConfigDict(extra="allow")

    lesson_id: str
    schema_version: int = 0
    title_en: str = ""
    activities: list[ActivityModel] = Field(default_factory=list)
    can_dos: list[dict[str, Any]] = Field(default_factory=list)
    english_notes: str | None = None
    portfolio_prompts: list[str] = Field(default_factory=list)


class IndexFile(BaseModel):
    model_config = ConfigDict(extra="allow")

    book_id: str
    book_title: str = ""
    schema_version: int = 0
    lessons: list[dict[str, Any]] = Field(default_factory=list)


def validate_lesson_dict(data: dict) -> dict:
    """Return data with defaults; does not drop extra YAML fields."""
    model = LessonFile.model_validate(data)
    out = dict(data)
    out["schema_version"] = model.schema_version
    return out
