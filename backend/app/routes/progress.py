from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.app.curriculum_loader import load_lesson
from backend.app.db import CanDoProgress, ChatSession, LessonProgress, get_db
from backend.app.lesson_progress import lesson_progress_snapshot
from backend.app.lesson_unlock import is_lesson_unlocked

router = APIRouter()

_PHASE_HINT = {
    "lesson_intro": "Just getting started",
    "intro_chat": "Warm-up questions",
    "book": "Book activities",
    "grammar": "Grammar practice",
    "can_do_quiz": "Can-do checks",
    "self_check": "Self-check",
    "lesson_complete": "Lesson complete",
}


def _resume_hint(db: Session, lesson_ids: list[str], lessons_out: list[dict]) -> dict | None:
    """Where the learner should continue — most recent in-progress session, else next open lesson."""
    by_id = {L["lesson_id"]: L for L in lessons_out}
    sessions = (
        db.query(ChatSession)
        .filter(ChatSession.lesson_id.in_(lesson_ids))
        .order_by(ChatSession.updated_at.desc(), ChatSession.id.desc())
        .all()
    )
    for sess in sessions:
        summary = by_id.get(sess.lesson_id)
        if not summary or not summary.get("unlocked"):
            continue
        if sess.state == "lesson_complete" or summary.get("mastered"):
            continue
        try:
            lesson = load_lesson(sess.lesson_id)
            snap = lesson_progress_snapshot(lesson, sess)
        except FileNotFoundError:
            snap = {"percent": 0, "label": "In progress", "phase": sess.state}
        return {
            "lesson_id": sess.lesson_id,
            "title_en": summary.get("title_en"),
            "title_jp": summary.get("title_jp"),
            "phase": snap.get("phase") or sess.state,
            "phase_label": snap.get("label") or _PHASE_HINT.get(sess.state, "In progress"),
            "phase_hint": _PHASE_HINT.get(sess.state, "In progress"),
            "percent": snap.get("percent") or 0,
            "has_session": True,
            "activity_id": sess.activity_id,
            "updated_at": sess.updated_at.isoformat() if sess.updated_at else None,
        }

    for summary in lessons_out:
        if summary.get("unlocked") and not summary.get("mastered"):
            return {
                "lesson_id": summary["lesson_id"],
                "title_en": summary.get("title_en"),
                "title_jp": summary.get("title_jp"),
                "phase": "lesson_intro",
                "phase_label": "Ready to start",
                "phase_hint": "Not started yet",
                "percent": 0,
                "has_session": False,
                "activity_id": None,
                "updated_at": None,
            }
    return None


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
        except Exception:  # noqa: BLE001 - keep the rail alive if one lesson YAML fails validation
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
                "title_jp": L.get("title_jp"),
                "topic_en": L.get("topic_en"),
                "unlocked": is_lesson_unlocked(db, lid),
                "mastered": lp.mastered if lp else False,
                "can_dos": can_dos,
            }
        )
    resume = _resume_hint(db, lesson_ids, out)
    return {
        "book_id": idx.get("book_id") or _active_book_id(),
        "book_title": idx.get("book_title"),
        "lessons": out,
        "resume": resume,
    }
