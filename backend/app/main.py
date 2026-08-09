"""Jtutor FastAPI backend — local-only tutor API."""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

# Prefer packaged / portable root when set
_ROOT_ENV = os.environ.get("JTUTOR_ROOT", "").strip()
ROOT = Path(_ROOT_ENV).resolve() if _ROOT_ENV else Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.app.db import init_db
from backend.app.config import settings
from backend.app.logging_setup import get_logger, setup_logging
from backend.app.routes import books, curriculum, health, log, media, progress, srs, tutor, voice

setup_logging()
_http_log = get_logger("http")

app = FastAPI(title="Jtutor", version="0.1.0")


@app.exception_handler(Exception)
async def unhandled_exception(_request: Request, exc: Exception):
    get_logger("app").exception("unhandled: %s", exc)
    return JSONResponse(status_code=500, content={"detail": str(exc)[:200]})


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5173",
        "http://localhost:5173",
        "http://127.0.0.1:8765",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, tags=["health"])
app.include_router(books.router, prefix="/books", tags=["books"])
app.include_router(curriculum.router, prefix="/curriculum", tags=["curriculum"])
app.include_router(progress.router, prefix="/progress", tags=["progress"])
app.include_router(tutor.router, prefix="/tutor", tags=["tutor"])
app.include_router(media.router, prefix="/media", tags=["media"])
app.include_router(voice.router, prefix="/voice", tags=["voice"])
app.include_router(srs.router, prefix="/srs", tags=["srs"])
app.include_router(log.router, prefix="/log", tags=["log"])

# Packaged / portable UI (Vite build + HashRouter). Prefer `ui/`, else desktop dist.
_UI_CANDIDATES = (
    settings.root_dir / "ui",
    settings.root_dir / "apps" / "desktop" / "dist",
)
_UI_DIR = next((p for p in _UI_CANDIDATES if (p / "index.html").is_file()), None)
if _UI_DIR is not None:
    _assets = _UI_DIR / "assets"
    if _assets.is_dir():
        app.mount("/assets", StaticFiles(directory=str(_assets)), name="ui-assets")

    @app.get("/")
    def ui_index():
        return FileResponse(_UI_DIR / "index.html")


@app.middleware("http")
async def log_requests(request, call_next):
    path = request.url.path
    if path.startswith("/health") and path == "/health":
        return await call_next(request)
    start = time.perf_counter()
    response = await call_next(request)
    ms = (time.perf_counter() - start) * 1000
    if path.startswith(("/tutor", "/voice", "/log")):
        _http_log.info(
            "%s %s -> %s %.0fms",
            request.method,
            path,
            response.status_code,
            ms,
        )
    return response


@app.on_event("startup")
def _startup() -> None:
    init_db()
    get_logger("app").info("api ready host=%s port=%s", settings.host, settings.port)
    import threading

    threading.Thread(target=lambda: __import__("backend.app.whisper_service", fromlist=["warm_whisper"]).warm_whisper(), daemon=True).start()


def main() -> None:
    import uvicorn

    uvicorn.run(
        "backend.app.main:app",
        host="127.0.0.1",
        port=8765,
        reload=False,
    )


if __name__ == "__main__":
    main()
