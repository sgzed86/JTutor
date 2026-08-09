"""Lesson flow controller (Tier 3.5 modular) — current step without DB side effects."""

from __future__ import annotations

from sqlalchemy.orm import Session

from backend.app import lesson_flow as flow
from backend.app.db import ChatSession
from backend.app.free_response import intro_step
from backend.app.self_check import self_check_step
from backend.app.session_flow import normalize_session


def current_step_snapshot(
    session: ChatSession,
    lesson: dict,
    db: Session,
    *,
    quiz_scenario_fn,
) -> dict:
    """Single resolver for tutor position (replaces duplicate orchestrator helpers)."""
    normalize_session(session)
    activity = flow.track_by_id(lesson, session.activity_id)
    idx = session.phase_index
    if session.phase == "book" and activity:
        return dict(flow.book_step(activity, lesson, idx)[2])
    if session.phase == "intro_chat":
        return dict(intro_step(lesson, idx)[2])
    if session.phase == "self_check":
        can_dos = lesson.get("can_dos") or []
        if idx < len(can_dos):
            return dict(self_check_step(can_dos[idx]))
    if session.phase == "can_do_quiz":
        can_dos = lesson.get("can_dos") or []
        if idx < len(can_dos):
            cd = can_dos[idx]
            scenario = quiz_scenario_fn(db, lesson, cd["id"])
            return dict(flow.quiz_step(cd, scenario, expect_speech=True))
    if session.phase == "grammar":
        return {"phase": "grammar", "expect_speech": True, "play_audio": [], "help": False}
    if session.phase == "lesson_intro":
        return {
            "phase": "intro",
            "expect_speech": False,
            "play_audio": [],
            "auto_advance_after_audio": True,
        }
    return {"phase": session.phase, "expect_speech": False, "play_audio": []}
