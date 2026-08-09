"""Lesson unlock checks for tutor API."""

from __future__ import annotations

from sqlalchemy.orm import Session

from backend.app.lesson_unlock import is_lesson_unlocked


def locked_response(db: Session, lesson_id: str) -> dict | None:
    if is_lesson_unlocked(db, lesson_id):
        return None
    return {
        "error": "Lesson locked. Master previous can-dos first.",
        "locked": True,
        "lesson_id": lesson_id,
    }
