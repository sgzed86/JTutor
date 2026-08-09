"""Book registry for build scripts — re-exports canonical backend registry (Tier 3.7)."""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.app.books import BOOKS as _META, BookInfo, get_book as _get_book_info


@dataclass(frozen=True)
class BookConfig:
    id: str
    title: str
    level: str
    content_dir: Path
    textbook_pdf: Path
    grammar_pdf: Path
    audio_prefix: str
    lesson_id_prefix: str
    unlock_first: tuple[str, ...]
    toc_en_pages: range
    toc_jp_pages: range


def _to_config(info: BookInfo) -> BookConfig:
    return BookConfig(
        id=info.id,
        title=info.title,
        level=info.level,
        content_dir=ROOT / "content" / info.content_subdir,
        textbook_pdf=ROOT / "assets" / info.textbook_pdf,
        grammar_pdf=ROOT / "assets" / info.grammar_pdf,
        audio_prefix=info.audio_prefix,
        lesson_id_prefix=info.lesson_prefix,
        unlock_first=info.unlock_first,
        toc_en_pages=range(info.toc_en_pages[0], info.toc_en_pages[-1] + 1)
        if info.toc_en_pages
        else range(0),
        toc_jp_pages=range(info.toc_jp_pages[0], info.toc_jp_pages[-1] + 1)
        if info.toc_jp_pages
        else range(0),
    )


def get_book(book_id: str) -> BookConfig:
    try:
        return _to_config(_get_book_info(book_id))
    except KeyError:
        raise SystemExit(f"Unknown book '{book_id}'. Choose: {', '.join(_META)}")


BOOKS: dict[str, BookConfig] = {bid: _to_config(_META[bid]) for bid in _META}
