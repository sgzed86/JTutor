from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import FileResponse, Response

from backend.app.books import BOOKS, get_book
from backend.app.config import settings
from backend.app.curriculum_loader import _active_book_id, resolve_asset
from backend.app.errors import AudioNotFound, InvalidRequest, PdfNotFound
from backend.app.logging_setup import get_logger

router = APIRouter()
_log = get_logger("media")


def _resolve_pdf(which: str, book: str | None) -> tuple[str, Path]:
    """Return (book_id, absolute pdf path) for textbook/grammar requests."""
    bid = book or _active_book_id()
    kind = which
    if kind in BOOKS:
        bid = kind
        kind = "textbook"
    if kind == "starter":
        bid, kind = "starter", "textbook"
    try:
        info = get_book(bid)
    except KeyError as e:
        raise InvalidRequest("Unknown book.") from e
    if kind in ("textbook", "book"):
        name = info.textbook_pdf
    elif kind in ("grammar", "worksheets"):
        name = info.grammar_pdf
    else:
        name = "Grammar_Worksheets_X.pdf" if kind != "starter" else info.textbook_pdf
    assets = settings.assets_dir.resolve()
    path = (assets / name).resolve()
    if assets not in path.parents:
        raise InvalidRequest("Invalid PDF path.")
    if not path.is_file():
        raise PdfNotFound(detail=name)
    return bid, path


@router.get("/audio")
def get_audio(path: str):
    """Serve an MP3 by relative path under project root (must be under assets/audio)."""
    rel = path.replace("\\", "/")
    if ".." in rel or not rel.startswith("assets/audio/"):
        raise InvalidRequest("Invalid audio path.")
    file_path = resolve_asset(rel)
    if not file_path.is_file():
        raise AudioNotFound(detail=rel)
    return FileResponse(file_path, media_type="audio/mpeg", filename=file_path.name)


@router.get("/pdf")
def get_pdf(which: str = "textbook", book: str | None = None):
    """
    which: textbook | grammar
    book: starter | elementary1 (default = active book)
    Legacy: which=starter → starter textbook; which=grammar → starter grammar.
    """
    _bid, path = _resolve_pdf(which, book)
    return FileResponse(path, media_type="application/pdf", filename=path.name)


@router.get("/pdf-page")
def get_pdf_page(
    page: int,
    which: str = "textbook",
    book: str | None = None,
    scale: float = 1.6,
):
    """Rasterize one PDF page to JPEG for in-app viewing (Electron can't embed huge PDFs)."""
    if page < 1:
        raise InvalidRequest("Page must be >= 1.")
    scale = max(1.0, min(float(scale or 1.6), 2.5))
    bid, pdf_path = _resolve_pdf(which, book)

    cache_dir = settings.data_dir / "pdf-page-cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    # One file per book/page/scale; rebuild if the source PDF is newer.
    cache_name = f"{bid}_{which}_p{page}_s{scale:.1f}.jpg"
    cache_path = cache_dir / cache_name
    try:
        if cache_path.is_file() and cache_path.stat().st_mtime >= pdf_path.stat().st_mtime:
            return FileResponse(cache_path, media_type="image/jpeg", filename=cache_name)
    except OSError:
        pass

    try:
        import pymupdf
    except ImportError as e:
        raise InvalidRequest(
            "PDF page preview needs PyMuPDF. Run: pip install pymupdf"
        ) from e

    try:
        doc = pymupdf.open(pdf_path)
    except Exception as e:  # noqa: BLE001 - surface as a typed media error
        _log.warning("pdf open failed path=%s err=%s", pdf_path, e)
        raise PdfNotFound(detail=pdf_path.name) from e

    try:
        if page > doc.page_count:
            raise InvalidRequest(f"Page {page} is past the end of this PDF ({doc.page_count} pages).")
        pix = doc.load_page(page - 1).get_pixmap(matrix=pymupdf.Matrix(scale, scale), alpha=False)
        jpeg = pix.tobytes("jpeg")
    finally:
        doc.close()

    try:
        cache_path.write_bytes(jpeg)
    except OSError as e:
        _log.warning("pdf page cache write failed: %s", e)
        return Response(content=jpeg, media_type="image/jpeg")

    return FileResponse(cache_path, media_type="image/jpeg", filename=cache_name)
