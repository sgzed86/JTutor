"""Soft Can-do self-check (stars + comment) — never gates unlocks."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy.orm import Session

from backend.app.db import CanDoProgress


def self_check_step(can_do: dict) -> dict:
    return {
        "phase": "self_check",
        "book_mode": "self_check",
        "book_substep": "rate",
        "can_do_id": can_do.get("id"),
        "statement_en": can_do.get("statement_en"),
        "statement_jp": can_do.get("statement_jp"),
        "expect_speech": False,
        "auto_advance_after_audio": False,
        "play_audio": [],
        "instruction_en": "How well could you do this Can-do? Rate yourself (optional comment).",
    }


def save_self_check(
    db: Session,
    lesson_id: str,
    can_do_id: str,
    stars: int,
    comment: str = "",
) -> CanDoProgress:
    stars = max(1, min(3, int(stars)))
    row = db.get(CanDoProgress, can_do_id)
    if row is None:
        row = CanDoProgress(can_do_id=can_do_id, lesson_id=lesson_id)
        db.add(row)
    row.lesson_id = lesson_id
    row.self_stars = stars
    row.self_comment = (comment or "").strip()[:500] or None
    row.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(row)
    return row


def self_check_summary(db: Session, lesson_id: str, can_dos: list[dict]) -> list[dict]:
    out = []
    for c in can_dos:
        cid = c.get("id")
        row = db.get(CanDoProgress, cid) if cid else None
        out.append(
            {
                "can_do_id": cid,
                "statement_en": c.get("statement_en"),
                "self_stars": row.self_stars if row else None,
                "self_comment": row.self_comment if row else None,
            }
        )
    return out
