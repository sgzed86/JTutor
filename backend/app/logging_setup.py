"""File + console logging for debugging tutor flow."""

from __future__ import annotations

import json
import logging
import sys
from logging.handlers import RotatingFileHandler
from typing import Any

from backend.app.config import settings

_CONFIGURED = False
LOG_NAME = "jtutor"


def setup_logging() -> logging.Logger:
    global _CONFIGURED
    logger = logging.getLogger(LOG_NAME)
    if _CONFIGURED:
        return logger

    level_name = (settings.log_level or "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)
    logger.setLevel(level)

    fmt = logging.Formatter(
        "%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )

    log_path = settings.log_path
    log_path.parent.mkdir(parents=True, exist_ok=True)
    file_handler = RotatingFileHandler(
        log_path,
        maxBytes=2_000_000,
        backupCount=4,
        encoding="utf-8",
    )
    file_handler.setFormatter(fmt)
    file_handler.setLevel(level)
    logger.addHandler(file_handler)

    console = logging.StreamHandler(sys.stderr)
    console.setFormatter(fmt)
    console.setLevel(level)
    logger.addHandler(console)

    logger.propagate = False
    _CONFIGURED = True
    logger.info("logging started path=%s level=%s", log_path, level_name)
    return logger


def get_logger(component: str) -> logging.Logger:
    setup_logging()
    return logging.getLogger(f"{LOG_NAME}.{component}")


def log_event(component: str, event: str, **fields: Any) -> None:
    """Structured one-line event for grep / sharing logs."""
    get_logger(component).info("%s %s", event, _format_fields(fields))


def _format_fields(fields: dict[str, Any]) -> str:
    if not fields:
        return ""
    safe: dict[str, Any] = {}
    for k, v in fields.items():
        if isinstance(v, str) and len(v) > 500:
            safe[k] = v[:500] + "…"
        else:
            safe[k] = v
    try:
        return json.dumps(safe, ensure_ascii=False, default=str)
    except TypeError:
        return str(safe)


def read_log_tail(max_lines: int = 200) -> list[str]:
    path = settings.log_path
    if not path.is_file():
        return []
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []
    lines = text.splitlines()
    if max_lines <= 0:
        return lines
    return lines[-max_lines:]
