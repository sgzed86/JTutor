"""Pytest configuration.

Every test runs against a throwaway SQLite database. `JTUTOR_DATA_DIR` has to be
set before `backend.app` is imported for the first time, because `config.py` and
`db.py` both resolve paths at import time.
"""

from __future__ import annotations

import os
import shutil
import sys
import tempfile
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

_TMP_DATA = Path(tempfile.mkdtemp(prefix="jtutor-tests-"))
os.environ.setdefault("JTUTOR_ROOT", str(REPO_ROOT))
os.environ["JTUTOR_DATA_DIR"] = str(_TMP_DATA)
os.environ.setdefault("LOG_LEVEL", "WARNING")


def pytest_unconfigure(config) -> None:  # noqa: ARG001
    shutil.rmtree(_TMP_DATA, ignore_errors=True)


@pytest.fixture()
def no_llm(monkeypatch):
    """Force the Ollama-backed paths onto their deterministic fallbacks."""
    from backend.app import ollama_client

    async def _refuse(*_args, **_kwargs):
        raise RuntimeError("ollama disabled in tests")

    monkeypatch.setattr(ollama_client, "chat", _refuse)
    return _refuse


@pytest.fixture()
def clean_db():
    """Truncate every table so each test starts from a known state."""
    from backend.app.db import Base, engine, init_db

    Base.metadata.drop_all(bind=engine)
    init_db()
    yield
    Base.metadata.drop_all(bind=engine)
    init_db()
