from __future__ import annotations

from pathlib import Path

import yaml

from backend.app.books import BOOKS, book_for_lesson_id, content_dir_for_book, content_dir_for_lesson
from backend.app.config import settings


def _active_book_id() -> str:
    # Prefer DB setting when available
    try:
        from backend.app.db import SessionLocal, SettingRow

        with SessionLocal() as db:
            row = db.get(SettingRow, "active_book")
            if row and row.value in BOOKS:
                return row.value
    except Exception as exc:  # noqa: BLE001 - fall back to the env default
        from backend.app.logging_setup import get_logger

        get_logger("curriculum").warning("could not read active book: %s", exc)
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


# Parsed YAML cache keyed by path, invalidated on (mtime, size). Lesson files are
# static at runtime but load_lesson() is called many times per tutor turn, and
# re-parsing a 100 KB YAML each time dominated request latency.
_yaml_cache: dict[str, tuple[float, int, dict]] = {}


def _load_yaml_cached(path: Path) -> dict | None:
    try:
        stat = path.stat()
    except OSError:
        return None
    key = str(path)
    cached = _yaml_cache.get(key)
    if cached and cached[0] == stat.st_mtime and cached[1] == stat.st_size:
        return cached[2]
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    _yaml_cache[key] = (stat.st_mtime, stat.st_size, data)
    return data


def clear_curriculum_cache() -> None:
    _yaml_cache.clear()


# NOTE: loaders return the cached object by reference. Callers must treat lesson
# and activity dicts as read-only; copy before mutating.


def load_index(book_id: str | None = None) -> dict:
    bid = book_id or _active_book_id()
    path = content_dir_for_book(bid) / "index.yaml"
    data = _load_yaml_cached(path)
    if data is None:
        return {"book_id": bid, "lessons": []}
    data.setdefault("book_id", bid)
    return data


def load_lesson(lesson_id: str) -> dict:
    path = content_dir_for_lesson(lesson_id) / f"{lesson_id}.yaml"
    data = _load_yaml_cached(path)
    if data is None:
        raise FileNotFoundError(lesson_id)
    data.setdefault("book_id", book_for_lesson_id(lesson_id).id)
    return data


def list_lessons(book_id: str | None = None) -> list[dict]:
    return load_index(book_id).get("lessons", [])


def resolve_asset(rel: str) -> Path:
    return settings.root_dir / rel
