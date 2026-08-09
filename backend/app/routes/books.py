from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.app.curriculum_loader import list_books, load_index, set_active_book

router = APIRouter()


class SetBookBody(BaseModel):
    book_id: str


@router.get("")
def books_index():
    return {"books": list_books(), "active": next((b["id"] for b in list_books() if b["active"]), "starter")}


@router.post("/active")
def set_book(body: SetBookBody):
    try:
        bid = set_active_book(body.book_id)
    except KeyError:
        raise HTTPException(404, "Unknown book") from None
    idx = load_index(bid)
    return {"ok": True, "active": bid, "lesson_count": len(idx.get("lessons") or [])}
