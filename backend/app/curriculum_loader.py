from __future__ import annotations

import copy
from pathlib import Path

import yaml

from backend.app.books import BOOKS, book_for_lesson_id, content_dir_for_book, content_dir_for_lesson, get_book
from backend.app.config import settings

_lesson_cache: dict[str, tuple[float, dict]] = {}
_index_cache: dict[str, tuple[float, dict]] = {}


def _active_book_id() -> str:
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
    _index_cache.clear()
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


def _cached_yaml(path: Path, cache: dict[str, tuple[float, dict]]) -> dict:
    key = str(path.resolve())
    mtime = path.stat().st_mtime if path.is_file() else 0.0
    hit = cache.get(key)
    if hit and hit[0] == mtime:
        return copy.deepcopy(hit[1])
    if not path.exists():
        data: dict = {}
    else:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    cache[key] = (mtime, data)
    return copy.deepcopy(data)


def load_index(book_id: str | None = None) -> dict:
    bid = book_id or _active_book_id()
    path = content_dir_for_book(bid) / "index.yaml"
    if not path.exists():
        return {"book_id": bid, "lessons": []}
    data = _cached_yaml(path, _index_cache)
    data.setdefault("book_id", bid)
    if not data.get("book_title"):
        data["book_title"] = get_book(bid).title
    data.setdefault("schema_version", 0)
    return data


def load_lesson(lesson_id: str) -> dict:
    path = content_dir_for_lesson(lesson_id) / f"{lesson_id}.yaml"
    if not path.exists():
        raise FileNotFoundError(lesson_id)
    data = _cached_yaml(path, _lesson_cache)
    data.setdefault("book_id", book_for_lesson_id(lesson_id).id)
    if "schema_version" not in data:
        data["schema_version"] = 0
    return data


def list_lessons(book_id: str | None = None) -> list[dict]:
    return load_index(book_id).get("lessons", [])


def resolve_asset(rel: str) -> Path:
    return settings.root_dir / rel
