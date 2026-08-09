from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.app import orchestrator
from backend.app.db import get_db

router = APIRouter()


class ChatIn(BaseModel):
    text: str
    spoken: bool = False


class SelfCheckIn(BaseModel):
    can_do_id: str
    stars: int
    comment: str = ""


@router.post("/{lesson_id}/start")
async def start(lesson_id: str, db: Session = Depends(get_db)):
    try:
        return await orchestrator.start_or_resume(db, lesson_id)
    except FileNotFoundError:
        raise HTTPException(404, "Lesson not found")


@router.post("/{lesson_id}/reset")
async def reset(lesson_id: str, db: Session = Depends(get_db)):
    try:
        return await orchestrator.reset_lesson(db, lesson_id)
    except FileNotFoundError:
        raise HTTPException(404, "Lesson not found")


@router.post("/{lesson_id}/advance")
async def advance(lesson_id: str, db: Session = Depends(get_db)):
    try:
        return await orchestrator.advance(db, lesson_id)
    except FileNotFoundError:
        raise HTTPException(404, "Lesson not found")


@router.post("/{lesson_id}/jump-can-do")
async def jump_can_do(
    lesson_id: str,
    reset_can_do: bool = False,
    db: Session = Depends(get_db),
):
    try:
        out = await orchestrator.jump_to_can_do_quiz(db, lesson_id, reset_can_do=reset_can_do)
        if out.get("error"):
            raise HTTPException(400, out["error"])
        return out
    except FileNotFoundError:
        raise HTTPException(404, "Lesson not found")


@router.post("/{lesson_id}/message")
async def message(lesson_id: str, body: ChatIn, db: Session = Depends(get_db)):
    try:
        return await orchestrator.user_message(db, lesson_id, body.text, spoken=body.spoken)
    except FileNotFoundError:
        raise HTTPException(404, "Lesson not found")


@router.post("/{lesson_id}/ask")
async def ask(lesson_id: str, body: ChatIn, db: Session = Depends(get_db)):
    try:
        return await orchestrator.answer_question(db, lesson_id, body.text, spoken=body.spoken)
    except FileNotFoundError:
        raise HTTPException(404, "Lesson not found")


@router.post("/{lesson_id}/self-check")
async def self_check(lesson_id: str, body: SelfCheckIn, db: Session = Depends(get_db)):
    """Soft Can-do self-rating (1–3 stars). Does not affect unlock logic."""
    try:
        out = await orchestrator.submit_self_check(
            db,
            lesson_id,
            can_do_id=body.can_do_id,
            stars=body.stars,
            comment=body.comment,
        )
        if out.get("error"):
            raise HTTPException(400, out["error"])
        return out
    except FileNotFoundError:
        raise HTTPException(404, "Lesson not found")
