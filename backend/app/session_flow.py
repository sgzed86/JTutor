"""Canonical lesson phase + index (Tier 3.2). Keeps legacy state/quiz_index in sync."""

from __future__ import annotations

from backend.app.db import ChatSession

VALID_PHASES = frozenset(
    {
        "lesson_intro",
        "intro_chat",
        "book",
        "grammar",
        "can_do_quiz",
        "self_check",
        "lesson_complete",
    }
)


def normalize_session(session: ChatSession) -> None:
    """Align phase/phase_index with state/quiz_index (legacy rows + new columns)."""
    st = session.state or "lesson_intro"
    if st not in VALID_PHASES:
        st = "lesson_intro"
        session.state = st
    if not getattr(session, "phase", None):
        session.phase = st
    elif session.phase not in VALID_PHASES:
        session.phase = st
    idx = int(session.quiz_index or 0)
    if getattr(session, "phase_index", None) is None:
        session.phase_index = idx
    else:
        session.phase_index = int(session.phase_index)
    # Legacy mirror: within a phase, quiz_index is the sub-index.
    if session.phase == st:
        session.quiz_index = session.phase_index
    else:
        session.state = session.phase
        session.quiz_index = session.phase_index


def enter_phase(session: ChatSession, phase: str, *, index: int = 0) -> None:
    if phase not in VALID_PHASES:
        phase = "lesson_intro"
    session.phase = phase
    session.state = phase
    session.phase_index = int(index)
    session.quiz_index = session.phase_index


def set_phase_index(session: ChatSession, index: int) -> None:
    session.phase_index = int(index)
    session.quiz_index = session.phase_index


def bump_phase_index(session: ChatSession) -> int:
    session.phase_index = int(session.phase_index or 0) + 1
    session.quiz_index = session.phase_index
    return session.phase_index


def phase_payload_fields(session: ChatSession) -> dict:
    normalize_session(session)
    return {
        "phase": session.phase,
        "phase_index": session.phase_index,
        "quiz_index": session.quiz_index,
    }
