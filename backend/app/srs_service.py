"""FSRS spaced repetition service."""

from __future__ import annotations

from datetime import UTC, datetime

from fsrs import Card, Rating, Scheduler, State
from sqlalchemy.orm import Session

from backend.app.config import settings
from backend.app.db import SrsCard, SrsReview

_scheduler = Scheduler()


def _aware(dt: datetime | None) -> datetime | None:
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt


def _naive(dt: datetime | None) -> datetime | None:
    if dt is None:
        return None
    if dt.tzinfo is not None:
        return dt.astimezone(UTC).replace(tzinfo=None)
    return dt


def _to_fsrs_card(row: SrsCard) -> Card:
    card = Card()
    card.due = _aware(row.due) or datetime.now(UTC)
    card.stability = row.stability if row.stability else None
    card.difficulty = row.difficulty if row.difficulty else None
    try:
        card.state = State(row.state) if row.state else State.Learning
    except Exception:
        card.state = State.Learning
    if row.last_review:
        card.last_review = _aware(row.last_review)
    return card


def _apply_fsrs(row: SrsCard, card: Card) -> None:
    row.due = _naive(card.due) or datetime.utcnow()
    row.stability = float(card.stability or 0)
    row.difficulty = float(card.difficulty or 0)
    row.state = int(card.state.value) if card.state is not None else 0
    row.last_review = _naive(card.last_review)
    row.reps = int(row.reps or 0) + 1


def enqueue_vocab(
    db: Session,
    lesson_id: str,
    phrases: list[str],
    can_do_id: str | None = None,
) -> int:
    created = 0
    for ph in phrases:
        ph = (ph or "").strip()
        if len(ph) < 2:
            continue
        exists = (
            db.query(SrsCard)
            .filter(SrsCard.lesson_id == lesson_id, SrsCard.front == ph, SrsCard.card_type == "vocab_recognition")
            .first()
        )
        if exists:
            continue
        db.add(
            SrsCard(
                card_type="vocab_recognition",
                lesson_id=lesson_id,
                can_do_id=can_do_id,
                front=ph,
                back=f"Recall meaning / reading for: {ph}",
                due=datetime.utcnow(),
            )
        )
        db.add(
            SrsCard(
                card_type="vocab_production",
                lesson_id=lesson_id,
                can_do_id=can_do_id,
                front=f"Say in Japanese (from lesson {lesson_id}): concept related to 「{ph}」",
                back=ph,
                due=datetime.utcnow(),
            )
        )
        created += 2
    db.commit()
    return created


def enqueue_from_gaps(
    db: Session,
    lesson_id: str,
    can_do_id: str,
    gaps: list[str],
    user_text: str,
) -> int:
    created = 0
    for g in gaps:
        g = (g or "").strip()
        if not g:
            continue
        exists = (
            db.query(SrsCard)
            .filter(SrsCard.front == g, SrsCard.can_do_id == can_do_id)
            .first()
        )
        if exists:
            continue
        db.add(
            SrsCard(
                card_type="can_do_recall",
                lesson_id=lesson_id,
                can_do_id=can_do_id,
                front=f"Produce: {g}",
                back=g,
                due=datetime.utcnow(),
            )
        )
        created += 1
    db.commit()
    return created


def enqueue_grammar(db: Session, lesson_id: str, points: list[str]) -> int:
    created = 0
    for p in points:
        p = (p or "").strip()
        if len(p) < 2:
            continue
        exists = (
            db.query(SrsCard)
            .filter(SrsCard.lesson_id == lesson_id, SrsCard.front == p, SrsCard.card_type == "grammar")
            .first()
        )
        if exists:
            continue
        db.add(
            SrsCard(
                card_type="grammar",
                lesson_id=lesson_id,
                front=p,
                back=f"Explain / use this pattern: {p}",
                due=datetime.utcnow(),
            )
        )
        created += 1
    db.commit()
    return created


def due_cards(db: Session, limit: int | None = None) -> list[SrsCard]:
    limit = limit or settings.srs_daily_review_cap
    now = datetime.utcnow()
    return (
        db.query(SrsCard)
        .filter(SrsCard.due <= now)
        .order_by(SrsCard.due.asc())
        .limit(limit)
        .all()
    )


def review_card(db: Session, card_id: int, rating: int) -> SrsCard:
    row = db.get(SrsCard, card_id)
    if row is None:
        raise KeyError(card_id)
    card = _to_fsrs_card(row)
    rating_map = {1: Rating.Again, 2: Rating.Hard, 3: Rating.Good, 4: Rating.Easy}
    r = rating_map.get(rating, Rating.Good)
    updated, _review_log = _scheduler.review_card(card, r)
    _apply_fsrs(row, updated)
    db.add(SrsReview(card_id=card_id, rating=rating))
    db.commit()
    db.refresh(row)
    return row


def card_to_dict(row: SrsCard) -> dict:
    return {
        "id": row.id,
        "card_type": row.card_type,
        "lesson_id": row.lesson_id,
        "can_do_id": row.can_do_id,
        "front": row.front,
        "back": row.back,
        "audio_path": row.audio_path,
        "due": row.due.isoformat() if row.due else None,
        "reps": row.reps,
        "state": row.state,
    }
