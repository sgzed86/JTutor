"""Lesson unlock checks for tutor API."""

from __future__ import annotations

from sqlalchemy.orm import Session

from backend.app.lesson_unlock import is_lesson_unlocked


def require_unlocked(lesson_id: str, db: Session) -> None:
    from fastapi import HTTPException

    if block := locked_response(db, lesson_id):
        raise HTTPException(403, block.get("error") or "Lesson locked")


def locked_response(db: Session, lesson_id: str) -> dict | None:
    if is_lesson_unlocked(db, lesson_id):
        return None
    return {
        "error": "Lesson locked. Master previous can-dos first.",
        "locked": True,
        "lesson_id": lesson_id,
    }
