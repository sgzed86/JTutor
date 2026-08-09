from __future__ import annotations

from fastapi import APIRouter, HTTPException

from backend.app import srs_service
from backend.app.curriculum_loader import load_lesson
from backend.app.db import SessionLocal

router = APIRouter()


@router.get("")
def curriculum_index():
    from backend.app.curriculum_loader import _active_book_id, load_index

    idx = load_index()
    return {
        "book_id": idx.get("book_id") or _active_book_id(),
        "book_title": idx.get("book_title"),
        "lessons": idx.get("lessons") or [],
    }


@router.get("/{lesson_id}")
def get_lesson(lesson_id: str):
    try:
        lesson = load_lesson(lesson_id)
    except FileNotFoundError:
        raise HTTPException(404, "Lesson not found") from None
    return lesson


@router.post("/{lesson_id}/seed-srs")
def seed_srs(lesson_id: str):
    try:
        lesson = load_lesson(lesson_id)
    except FileNotFoundError:
        raise HTTPException(404, "Lesson not found") from None
    with SessionLocal() as db:
        n = srs_service.enqueue_vocab(
            db,
            lesson_id,
            [v.get("jp") for v in (lesson.get("vocab") or []) if v.get("jp")],
        )
        g = srs_service.enqueue_grammar(
            db,
            lesson_id,
            [x.get("point") for x in (lesson.get("grammar") or []) if x.get("point")],
        )
        # Also key phrases from activities
        phrases = []
        for a in lesson.get("activities") or []:
            phrases.extend(a.get("key_phrases") or [])
        n2 = srs_service.enqueue_vocab(db, lesson_id, phrases)
    return {"vocab_cards": n + n2, "grammar_cards": g}
