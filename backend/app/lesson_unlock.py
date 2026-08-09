"""Which lessons the learner may open (progression + DB flags)."""

from __future__ import annotations

from sqlalchemy.orm import Session

from backend.app.books import book_for_lesson_id, format_lesson_id, parse_lesson_num
from backend.app.curriculum_loader import list_lessons
from backend.app.db import LessonProgress


def next_lesson_id(lesson_id: str) -> str | None:
    n = parse_lesson_num(lesson_id)
    if n is None:
        return None
    book = book_for_lesson_id(lesson_id)
    nxt = format_lesson_id(book.id, n + 1)
    if any(x["lesson_id"] == nxt for x in list_lessons(book.id)):
        return nxt
    return None


def is_lesson_unlocked(db: Session, lesson_id: str) -> bool:
    book = book_for_lesson_id(lesson_id)
    # Classroom / first lesson always open
    if lesson_id in ("L00",) or lesson_id == format_lesson_id(book.id, 1):
        return True
    lp = db.get(LessonProgress, lesson_id)
    if lp and lp.unlocked:
        return True
    n = parse_lesson_num(lesson_id)
    if n is None:
        return False
    if n <= 1:
        return True
    prev = db.get(LessonProgress, format_lesson_id(book.id, n - 1))
    return bool(prev and prev.mastered)
