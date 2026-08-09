from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.app.curriculum_loader import load_lesson
from backend.app.db import CanDoProgress, LessonProgress, get_db
from backend.app.lesson_unlock import is_lesson_unlocked

router = APIRouter()


@router.get("")
def progress_overview(db: Session = Depends(get_db)):
    from backend.app.curriculum_loader import _active_book_id, load_index

    idx = load_index()
    lessons = idx.get("lessons") or []
    lesson_ids = [L["lesson_id"] for L in lessons]
    lp_rows = {
        r.lesson_id: r
        for r in db.query(LessonProgress).filter(LessonProgress.lesson_id.in_(lesson_ids)).all()
    }
    all_can_do_ids: list[str] = []
    lesson_can_map: dict[str, list[dict]] = {}
    for lid in lesson_ids:
        try:
            lesson = load_lesson(lid)
            cds = lesson.get("can_dos") or []
            lesson_can_map[lid] = cds
            all_can_do_ids.extend(c["id"] for c in cds if c.get("id"))
        except FileNotFoundError:
            lesson_can_map[lid] = []
    cp_rows = {
        r.can_do_id: r
        for r in db.query(CanDoProgress).filter(CanDoProgress.can_do_id.in_(all_can_do_ids)).all()
    }
    out = []
    for L in lessons:
        lid = L["lesson_id"]
        lp = lp_rows.get(lid)
        can_dos = []
        for c in lesson_can_map.get(lid, []):
            cp = cp_rows.get(c["id"])
            can_dos.append(
                {
                    **c,
                    "passes": cp.passes if cp else 0,
                    "spoken_passes": cp.spoken_passes if cp else 0,
                    "best_score": cp.best_score if cp else 0,
                    "mastered": cp.mastered if cp else False,
                }
            )
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
