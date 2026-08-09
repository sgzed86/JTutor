"""Pydantic models for the lesson YAML.

These encode what the shipped content already looks like, with defaults for the
optional fields, so a curriculum rebuild cannot silently ship a lesson the tutor
cannot drive. Every field added here must be optional with a default — existing
files have to validate unchanged.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

BookMode = Literal[
    "listen_repeat",
    "listen_repeat_all",
    "listen_select",
    "dialog",
    "shadow_dialog",
    "pronunciation",
    "vocab_drill",
    "kana_trace",
    "culture_read",
    "repeat",
]


class Base(BaseModel):
    model_config = ConfigDict(extra="allow")


class PhraseMeta(Base):
    jp: str
    tags: list[str] = Field(default_factory=list)
    readings: str | None = None


class DialogLine(Base):
    speaker: Literal["partner", "learner"]
    jp: str


class Activity(Base):
    id: str
    kind: str
    book_activity: int | None = None
    can_do_id: str | None = None
    label: str | None = None
    audio: list[str] = Field(default_factory=list)
    key_phrases: list[str] = Field(default_factory=list)
    prompt_en: str | None = None
    # Optional, all defaulted — see docs/CURRICULUM_SCHEMA.md
    book_mode: BookMode = "listen_repeat"
    book_skip: bool = False
    picture_hint_en: str | None = None
    picture_has_image: bool = False
    dialog_script: list[DialogLine] = Field(default_factory=list)
    dialog_listen_audio: list[str] = Field(default_factory=list)
    book_section_jp: str | None = None
    book_section_en: str | None = None
    book_scene_en: str | None = None
    phrase_meta: list[PhraseMeta] = Field(default_factory=list)
    notes_en: str | None = None
    estimated_seconds: int | None = None

    @field_validator("audio", "dialog_listen_audio")
    @classmethod
    def _audio_paths_look_right(cls, v: list[str]) -> list[str]:
        for p in v:
            if p and not p.replace("\\", "/").startswith("assets/audio/"):
                raise ValueError(f"audio path must live under assets/audio/: {p}")
        return v


class Rubric(Base):
    must_include: list[str] = Field(default_factory=list)
    min_score: int = 80


class CanDo(Base):
    id: str
    can_do_number: int | None = None
    statement_en: str | None = None
    statement_jp: str | None = None
    activity_hint: str | None = None
    rubric: Rubric = Field(default_factory=Rubric)


class QuizScenario(Base):
    can_do_id: str
    partner_jp: str | None = None
    expected: list[str] = Field(default_factory=list)
    hint_en: str | None = None


class GrammarPoint(Base):
    point: str
    worksheet_pages: list[Any] = Field(default_factory=list)


class VocabItem(Base):
    jp: str | None = None
    en: str | None = None


class Lesson(Base):
    schema_version: int = 1
    lesson_id: str
    book_id: str | None = None
    lesson: int | None = None
    title_en: str | None = None
    title_jp: str | None = None
    topic_en: str | None = None
    pdf_pages: list[int] = Field(default_factory=list)
    can_dos: list[CanDo] = Field(default_factory=list)
    activities: list[Activity] = Field(default_factory=list)
    grammar: list[GrammarPoint] = Field(default_factory=list)
    vocab: list[VocabItem] = Field(default_factory=list)
    quiz_bank: list[Any] = Field(default_factory=list)
    quiz_scenarios: list[QuizScenario] = Field(default_factory=list)
    intro_questions: list[Any] = Field(default_factory=list)
    english_notes: Any = None
    unlock_requires_mastery: bool = True


def validate_lesson(data: dict) -> Lesson:
    return Lesson.model_validate(data)


def lesson_issues(data: dict) -> list[str]:
    """Non-fatal content problems worth surfacing during a curriculum build."""
    issues: list[str] = []
    try:
        lesson = validate_lesson(data)
    except Exception as exc:  # noqa: BLE001 - reported as an issue string
        return [f"invalid: {exc}"]

    can_do_ids = {c.id for c in lesson.can_dos}
    for activity in lesson.activities:
        if activity.can_do_id and activity.can_do_id not in can_do_ids:
            issues.append(f"{activity.id}: can_do_id {activity.can_do_id!r} is not declared")
        if "book_mode" not in (data_activity(data, activity.id) or {}):
            issues.append(f"{activity.id}: no explicit book_mode (defaulting to listen_repeat)")
        if activity.book_mode == "dialog" and not activity.dialog_script:
            issues.append(f"{activity.id}: dialog mode without a dialog_script")
        if activity.book_mode == "dialog":
            speakers = {line.speaker for line in activity.dialog_script}
            if activity.dialog_script and speakers != {"partner", "learner"}:
                issues.append(f"{activity.id}: dialog_script is missing a speaker role")
    for scenario in lesson.quiz_scenarios:
        if scenario.can_do_id not in can_do_ids:
            issues.append(f"quiz_scenario references unknown can_do {scenario.can_do_id!r}")
    return issues


def data_activity(data: dict, activity_id: str) -> dict | None:
    for a in data.get("activities") or []:
        if a.get("id") == activity_id:
            return a
    return None
