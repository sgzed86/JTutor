from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.app import srs_service
from backend.app.db import SrsCard, get_db

router = APIRouter()


class ReviewIn(BaseModel):
    rating: int = Field(ge=1, le=4)


@router.get("/due")
def due(db: Session = Depends(get_db)):
    cards = srs_service.due_cards(db)
    return {"count": len(cards), "cards": [srs_service.card_to_dict(c) for c in cards]}


@router.post("/{card_id}/review")
def review(card_id: int, body: ReviewIn, db: Session = Depends(get_db)):
    try:
        row = srs_service.review_card(db, card_id, body.rating)
    except KeyError:
        raise HTTPException(404, "Card not found")
    return srs_service.card_to_dict(row)


@router.get("/stats")
def stats(db: Session = Depends(get_db)):
    total = db.query(SrsCard).count()
    due = len(srs_service.due_cards(db, limit=1000))
    return {"total": total, "due": due}
