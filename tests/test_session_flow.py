"""Session phase helpers."""

from __future__ import annotations

from backend.app.db import ChatSession
from backend.app.session_flow import enter_phase, normalize_session


def test_enter_phase_syncs_quiz_index():
    s = ChatSession(lesson_id="L01", state="book", quiz_index=3, phase="book", phase_index=0)
    enter_phase(s, "book", index=3)
    assert s.quiz_index == 3
    assert s.phase_index == 3


def test_normalize_legacy_session():
    s = ChatSession(lesson_id="L01", state="grammar", quiz_index=2)
    normalize_session(s)
    assert s.phase == "grammar"
    assert s.phase_index == 2
