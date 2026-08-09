"""Registered Irodori books available to the tutor."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from backend.app.config import settings


@dataclass(frozen=True)
class BookInfo:
    id: str
    title: str
    level: str
    lesson_prefix: str
    content_subdir: str
    textbook_pdf: str
    grammar_pdf: str


BOOKS: dict[str, BookInfo] = {
    "starter": BookInfo(
        id="starter",
        title="Irodori Starter (A1)",
        level="A1",
        lesson_prefix="L",
        content_subdir="starter",
        textbook_pdf="irodori_starter.pdf",
        grammar_pdf="Grammar_Worksheets_X.pdf",
    ),
    "elementary1": BookInfo(
        id="elementary1",
        title="Irodori Elementary 1 (A2)",
        level="A2",
        lesson_prefix="EL",
        content_subdir="elementary1",
        textbook_pdf="Elementary1.pdf",
        grammar_pdf="Grammar_Elementary_1.pdf",
    ),
}


def get_book(book_id: str | None) -> BookInfo:
    bid = book_id or "starter"
    if bid not in BOOKS:
        raise KeyError(bid)
    return BOOKS[bid]


def book_for_lesson_id(lesson_id: str) -> BookInfo:
    if lesson_id.startswith("EL"):
        return BOOKS["elementary1"]
    return BOOKS["starter"]


def content_dir_for_book(book_id: str | None = None) -> Path:
    info = get_book(book_id)
    return settings.root_dir / "content" / info.content_subdir


def content_dir_for_lesson(lesson_id: str) -> Path:
    return content_dir_for_book(book_for_lesson_id(lesson_id).id)


def parse_lesson_num(lesson_id: str) -> int | None:
    import re

    m = re.match(r"^(?:EL|L)(\d+)$", lesson_id)
    if not m:
        return None
    return int(m.group(1))


def format_lesson_id(book_id: str, n: int) -> str:
    prefix = get_book(book_id).lesson_prefix
    return f"{prefix}{n:02d}"
