"""Map curriculum activities to textbook PDF pages.

Irodori pages print CD codes like ``04-01``. Activities already reference those
tracks in ``audio`` paths (``X_[04-01]_kotoba1.mp3``), so matching the track
string in page text is far more accurate than linear interpolation.
"""

from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path

from backend.app.books import get_book
from backend.app.config import settings
from backend.app.logging_setup import get_logger

_log = get_logger("book_pages")

_TRACK_IN_PATH = re.compile(r"\[(\d{2})-(\d{2})\]")
_TRACK_LOOSE = re.compile(r"(?<!\d)(\d{2})-(\d{2})(?!\d)")


def track_tags_from_activity(activity: dict | None) -> list[str]:
    """Return CD tags like ``04-01`` found on the activity's audio paths."""
    if not activity:
        return []
    found: list[str] = []
    seen: set[str] = set()
    for raw in list(activity.get("audio") or []) + list(activity.get("dialog_listen_audio") or []):
        path = str(raw or "").replace("\\", "/")
        for m in _TRACK_IN_PATH.finditer(path):
            tag = f"{m.group(1)}-{m.group(2)}"
            if tag not in seen:
                seen.add(tag)
                found.append(tag)
        if not found:
            for m in _TRACK_LOOSE.finditer(Path(path).name):
                tag = f"{m.group(1)}-{m.group(2)}"
                if tag not in seen:
                    seen.add(tag)
                    found.append(tag)
    return found


def _textbook_pdf(book_id: str | None) -> Path | None:
    try:
        info = get_book(book_id or "starter")
    except KeyError:
        return None
    path = (settings.assets_dir / info.textbook_pdf).resolve()
    return path if path.is_file() else None


@lru_cache(maxsize=8)
def _page_text_index(pdf_path: str, start: int, end: int) -> dict[int, str]:
    """Load and cache plain text for a contiguous page range (1-based inclusive)."""
    try:
        import pymupdf
    except ImportError:
        _log.warning("pymupdf missing; cannot index textbook pages")
        return {}
    out: dict[int, str] = {}
    try:
        doc = pymupdf.open(pdf_path)
    except Exception as exc:  # noqa: BLE001
        _log.warning("could not open pdf %s: %s", pdf_path, exc)
        return {}
    try:
        for page in range(start, end + 1):
            if page < 1 or page > doc.page_count:
                continue
            out[page] = doc.load_page(page - 1).get_text("text") or ""
    finally:
        doc.close()
    return out


def find_page_for_tracks(
    tracks: list[str],
    *,
    book_id: str | None,
    page_start: int,
    page_end: int,
) -> int | None:
    """First page in range that contains any of the CD track tags."""
    if not tracks or page_start < 1:
        return None
    pdf = _textbook_pdf(book_id)
    if pdf is None:
        return None
    start, end = sorted((int(page_start), int(page_end)))
    index = _page_text_index(str(pdf), start, end)
    for track in tracks:
        for page in range(start, end + 1):
            text = index.get(page) or ""
            if track in text:
                return page
    return None


def resolve_activity_page(
    lesson: dict,
    activity: dict | None,
    pdf_pages: list[int],
) -> int | None:
    """Best textbook page for an activity within the lesson's pdf_pages range."""
    if activity and activity.get("pdf_page") is not None:
        try:
            return int(activity["pdf_page"])
        except (TypeError, ValueError):
            pass
    if not pdf_pages:
        return None
    start = int(pdf_pages[0])
    end = int(pdf_pages[-1]) if len(pdf_pages) > 1 else start
    if end < start:
        start, end = end, start

    tracks = track_tags_from_activity(activity)
    hit = find_page_for_tracks(
        tracks,
        book_id=lesson.get("book_id"),
        page_start=start,
        page_end=end,
    )
    if hit is not None:
        return hit
    return start
