from __future__ import annotations

from pathlib import Path

import yaml

from backend.app.books import BOOKS, book_for_lesson_id, content_dir_for_book, content_dir_for_lesson, get_book
from backend.app.config import settings


def _active_book_id() -> str:
    # Prefer DB setting when available
    try:
        from backend.app.db import SessionLocal, SettingRow

        with SessionLocal() as db:
            row = db.get(SettingRow, "active_book")
            if row and row.value in BOOKS:
                return row.value
    except Exception:
        pass
    return settings.active_book if settings.active_book in BOOKS else "starter"


def set_active_book(book_id: str) -> str:
    if book_id not in BOOKS:
        raise KeyError(book_id)
    from backend.app.db import SessionLocal, SettingRow

    with SessionLocal() as db:
        row = db.get(SettingRow, "active_book")
        if row is None:
            db.add(SettingRow(key="active_book", value=book_id))
        else:
            row.value = book_id
        db.commit()
    settings.active_book = book_id
    return book_id


def list_books() -> list[dict]:
    out = []
    active = _active_book_id()
    for bid, info in BOOKS.items():
        idx = content_dir_for_book(bid) / "index.yaml"
        out.append(
            {
                "id": bid,
                "title": info.title,
                "level": info.level,
                "available": idx.is_file(),
                "active": bid == active,
            }
        )
    return out


def load_index(book_id: str | None = None) -> dict:
    bid = book_id or _active_book_id()
    path = content_dir_for_book(bid) / "index.yaml"
    if not path.exists():
        return {"book_id": bid, "lessons": []}
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    data.setdefault("book_id", bid)
    return data


def load_lesson(lesson_id: str) -> dict:
    path = content_dir_for_lesson(lesson_id) / f"{lesson_id}.yaml"
    if not path.exists():
        raise FileNotFoundError(lesson_id)
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    data.setdefault("book_id", book_for_lesson_id(lesson_id).id)
    return data


def list_lessons(book_id: str | None = None) -> list[dict]:
    return load_index(book_id).get("lessons", [])


def resolve_asset(rel: str) -> Path:
    return settings.root_dir / rel
