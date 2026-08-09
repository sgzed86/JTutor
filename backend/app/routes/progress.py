from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.app.curriculum_loader import list_lessons, load_lesson
from backend.app.db import CanDoProgress, LessonProgress, get_db
from backend.app.lesson_unlock import is_lesson_unlocked

router = APIRouter()


@router.get("")
def progress_overview(db: Session = Depends(get_db)):
    from backend.app.curriculum_loader import _active_book_id, load_index

    idx = load_index()
    lessons = idx.get("lessons") or []
    out = []
    for L in lessons:
        lid = L["lesson_id"]
        lp = db.get(LessonProgress, lid)
        can_dos = []
        try:
            lesson = load_lesson(lid)
            for c in lesson.get("can_dos") or []:
                cp = db.get(CanDoProgress, c["id"])
                can_dos.append(
                    {
                        **c,
                        "passes": cp.passes if cp else 0,
                        "spoken_passes": cp.spoken_passes if cp else 0,
                        "best_score": cp.best_score if cp else 0,
                        "mastered": cp.mastered if cp else False,
                    }
                )
        except FileNotFoundError:
            pass
        out.append(
            {
                "lesson_id": lid,
                "book_id": L.get("book_id") or idx.get("book_id"),
                "title_en": L.get("title_en"),
                "topic_en": L.get("topic_en"),
                "unlocked": is_lesson_unlocked(db, lid),
                "mastered": lp.mastered if lp else False,
                "can_dos": can_dos,
            }
        )
    return {
        "book_id": idx.get("book_id") or _active_book_id(),
        "book_title": idx.get("book_title"),
        "lessons": out,
    }
