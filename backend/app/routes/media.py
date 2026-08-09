from __future__ import annotations

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from backend.app.books import BOOKS, get_book
from backend.app.config import settings
from backend.app.curriculum_loader import _active_book_id, resolve_asset

router = APIRouter()


@router.get("/audio")
def get_audio(path: str):
    """Serve an MP3 by relative path under project root (must be under assets/audio)."""
    rel = path.replace("\\", "/")
    if ".." in rel or not rel.startswith("assets/audio/"):
        raise HTTPException(400, "Invalid audio path")
    file_path = resolve_asset(rel)
    if not file_path.is_file():
        raise HTTPException(404, f"Audio not found: {rel}")
    return FileResponse(file_path, media_type="audio/mpeg", filename=file_path.name)


@router.get("/pdf")
def get_pdf(which: str = "textbook", book: str | None = None):
    """
    which: textbook | grammar
    book: starter | elementary1 (default = active book)
    Legacy: which=starter → starter textbook; which=grammar → starter grammar.
    """
    bid = book or _active_book_id()
    if which in BOOKS:
        # legacy: /pdf?which=starter
        bid = which
        which = "textbook"
    if which == "starter":
        bid, which = "starter", "textbook"
    try:
        info = get_book(bid)
    except KeyError:
        raise HTTPException(404, "Unknown book")
    if which in ("textbook", "book"):
        name = info.textbook_pdf
    elif which in ("grammar", "worksheets"):
        name = info.grammar_pdf
    else:
        # legacy Grammar_Worksheets_X
        name = "Grammar_Worksheets_X.pdf" if which != "starter" else info.textbook_pdf
    path = settings.assets_dir / name
    if not path.is_file():
        raise HTTPException(404, f"PDF not found: {name}")
    return FileResponse(path, media_type="application/pdf", filename=name)
