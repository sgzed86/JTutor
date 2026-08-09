"""Jtutor FastAPI backend — local-only tutor API."""

from __future__ import annotations

import asyncio
import os
import sys
import time
from contextlib import asynccontextmanager
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

from backend.app.config import settings  # noqa: E402
from backend.app.db import init_db  # noqa: E402
from backend.app.errors import JtutorError, Unauthorized, jtutor_error_handler  # noqa: E402
from backend.app.logging_setup import get_logger, setup_logging  # noqa: E402
from backend.app.routes import (  # noqa: E402
    books,
    curriculum,
    health,
    log,
    media,
    progress,
    srs,
    tutor,
    voice,
)
from backend.app.routes import settings as settings_routes  # noqa: E402
from backend.app.speech.stt import transcription_service  # noqa: E402
from backend.app.speech.tts import speech_service  # noqa: E402

setup_logging()
_http_log = get_logger("http")
_app_log = get_logger("app")

# Per-run token minted by the Electron supervisor. When unset (plain `uvicorn`
# during development) authentication is disabled.
APP_TOKEN = os.environ.get("JTUTOR_TOKEN", "").strip()
_OPEN_PATHS = ("/health", "/docs", "/openapi.json", "/redoc")


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    _app_log.info(
        "api ready host=%s port=%s data=%s token=%s",
        settings.host,
        settings.port,
        settings.data_dir,
        "on" if APP_TOKEN else "off",
    )
    # Warm the speech model off the request path so the first recording is not
    # the thing that pays for loading it.
    warm_task = asyncio.create_task(transcription_service.warm())
    try:
        yield
    finally:
        warm_task.cancel()
        speech_service.sweep_cache()
        transcription_service.shutdown()


app = FastAPI(title="Jtutor", version="0.2.0", lifespan=lifespan)

app.add_exception_handler(JtutorError, jtutor_error_handler)

# Loopback-only API. When the supervisor supplies a token the origin list is
# irrelevant, but keeping it tight avoids other local pages poking the API.
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"^https?://(127\.0\.0\.1|localhost)(:\d+)?$",
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def auth_and_log(request: Request, call_next):
    path = request.url.path
    if APP_TOKEN and request.method != "OPTIONS" and not path.startswith(_OPEN_PATHS):
        supplied = request.headers.get("x-jtutor-token") or request.query_params.get("token")
        if supplied != APP_TOKEN:
            err = Unauthorized()
            return JSONResponse(status_code=err.status_code, content=err.envelope())

    if path == "/health":
        return await call_next(request)
    start = time.perf_counter()
    response = await call_next(request)
    ms = (time.perf_counter() - start) * 1000
    if path.startswith(("/tutor", "/voice", "/log", "/settings")):
        _http_log.info("%s %s -> %s %.0fms", request.method, path, response.status_code, ms)
    return response


app.include_router(health.router, tags=["health"])
app.include_router(books.router, prefix="/books", tags=["books"])
app.include_router(curriculum.router, prefix="/curriculum", tags=["curriculum"])
app.include_router(progress.router, prefix="/progress", tags=["progress"])
app.include_router(tutor.router, prefix="/tutor", tags=["tutor"])
app.include_router(media.router, prefix="/media", tags=["media"])
app.include_router(voice.router, prefix="/voice", tags=["voice"])
app.include_router(srs.router, prefix="/srs", tags=["srs"])
app.include_router(log.router, prefix="/log", tags=["log"])
app.include_router(settings_routes.router, prefix="/settings", tags=["settings"])


@app.post("/internal/shutdown")
async def internal_shutdown():
    """Graceful stop requested by the desktop supervisor before it sends SIGTERM."""

    async def _stop() -> None:
        await asyncio.sleep(0.1)
        os.kill(os.getpid(), __import__("signal").SIGINT)

    asyncio.create_task(_stop())
    return {"ok": True, "stopping": True}


# ---------------------------------------------------------------------------
# Packaged / portable UI (Vite build + HashRouter). Resolved lazily so a UI
# built after the server started is still served.
_UI_CANDIDATES = (
    settings.root_dir / "ui",
    settings.root_dir / "apps" / "desktop" / "dist",
)


def _ui_dir() -> Path | None:
    return next((p for p in _UI_CANDIDATES if (p / "index.html").is_file()), None)


for _candidate in _UI_CANDIDATES:
    _assets = _candidate / "assets"
    if _assets.is_dir():
        app.mount("/assets", StaticFiles(directory=str(_assets)), name="ui-assets")
        break


@app.get("/")
def ui_index():
    ui = _ui_dir()
    if ui is None:
        return JSONResponse(
            status_code=404,
            content={
                "error": {
                    "code": "ui_not_built",
                    "message": "The desktop UI has not been built yet.",
                    "hint": "Run `npm run build:ui`, or use the Vite dev server.",
                    "retryable": False,
                }
            },
        )
    return FileResponse(ui / "index.html")


def main() -> None:
    import uvicorn

    uvicorn.run(app, host=settings.host, port=settings.port or 8765, log_config=None)


if __name__ == "__main__":
    main()
