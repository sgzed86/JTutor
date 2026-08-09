"""Book registry for Irodori Starter / Elementary 1 content pipelines."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class BookConfig:
    id: str
    title: str
    level: str
    content_dir: Path
    textbook_pdf: Path
    grammar_pdf: Path
    audio_prefix: str  # X_ starter, Y_ elementary1
    lesson_id_prefix: str  # L or EL
    unlock_first: tuple[str, ...]
    toc_en_pages: range
    toc_jp_pages: range


BOOKS: dict[str, BookConfig] = {
    "starter": BookConfig(
        id="starter",
        title="Irodori Starter (A1)",
        level="A1",
        content_dir=ROOT / "content" / "starter",
        textbook_pdf=ROOT / "assets" / "irodori_starter.pdf",
        grammar_pdf=ROOT / "assets" / "Grammar_Worksheets_X.pdf",
        audio_prefix="X_",
        lesson_id_prefix="L",
        unlock_first=("L00", "L01"),
        toc_en_pages=range(36, 42),
        toc_jp_pages=range(30, 36),
    ),
    "elementary1": BookConfig(
        id="elementary1",
        title="Irodori Elementary 1 (A2)",
        level="A2",
        content_dir=ROOT / "content" / "elementary1",
        textbook_pdf=ROOT / "assets" / "Elementary1.pdf",
        grammar_pdf=ROOT / "assets" / "Grammar_Elementary_1.pdf",
        audio_prefix="Y_",
        lesson_id_prefix="EL",
        unlock_first=("EL01",),
        toc_en_pages=range(36, 42),
        toc_jp_pages=range(30, 36),
    ),
}


def get_book(book_id: str) -> BookConfig:
    if book_id not in BOOKS:
        raise SystemExit(f"Unknown book '{book_id}'. Choose: {', '.join(BOOKS)}")
    return BOOKS[book_id]
