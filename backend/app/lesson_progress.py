"""Lesson progress fraction from tutor session state."""

from __future__ import annotations

from backend.app.book_modes import flow_substeps
from backend.app.db import ChatSession
from backend.app import lesson_flow as flow
from backend.app.free_response import intro_questions


def lesson_progress_snapshot(lesson: dict, session: ChatSession) -> dict:
    tracks = flow.book_tracks(lesson)
    n_tracks = max(len(tracks), 1)
    grammar_n = len(flow._grammar_for_lesson(lesson["lesson_id"]))
    can_n = len(lesson.get("can_dos") or [])
    intro_n = len(intro_questions(lesson))

    state = session.state or "lesson_intro"
    fraction = 0.0
    label = "Starting"

    if state == "lesson_intro":
        fraction = 0.02
        label = "Introduction"
    elif state == "intro_chat":
        if intro_n:
            fraction = 0.03 + min(session.quiz_index, intro_n) / intro_n * 0.05
            label = f"Warm-up · {min(session.quiz_index + 1, intro_n)}/{intro_n}"
        else:
            fraction = 0.05
            label = "Warm-up"
    elif state == "book":
        idx = flow.track_index(lesson, session.activity_id)
        act = flow.track_by_id(lesson, session.activity_id)
        subs = max(len(flow_substeps(act)), 1) if act else 1
        sub_frac = min(session.quiz_index, subs) / subs
        fraction = 0.08 + (idx + sub_frac) / n_tracks * 0.58
        label = f"Book · activity {idx + 1}/{n_tracks}"
    elif state == "grammar":
        if grammar_n:
            fraction = 0.68 + min(session.quiz_index, grammar_n) / grammar_n * 0.10
            label = f"Grammar · {min(session.quiz_index + 1, grammar_n)}/{grammar_n}"
        else:
            fraction = 0.72
            label = "Grammar"
    elif state == "can_do_quiz":
        if can_n:
            fraction = 0.78 + min(session.quiz_index, can_n) / can_n * 0.12
            label = f"Can-do · {min(session.quiz_index + 1, can_n)}/{can_n}"
        else:
            fraction = 0.88
            label = "Can-do check"
    elif state == "self_check":
        if can_n:
            fraction = 0.90 + min(session.quiz_index, can_n) / can_n * 0.08
            label = f"Self-check · {min(session.quiz_index + 1, can_n)}/{can_n}"
        else:
            fraction = 0.95
            label = "Self-check"
    elif state == "lesson_complete":
        fraction = 1.0
        label = "Lesson complete"

    fraction = min(1.0, max(0.0, fraction))
    return {
        "fraction": round(fraction, 3),
        "percent": int(round(fraction * 100)),
        "phase": state,
        "label": label,
    }
