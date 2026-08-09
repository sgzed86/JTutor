"""Lesson unlock enforcement."""

from __future__ import annotations

import os
import sys
import tempfile

ROOT = __file__.replace("/tests/test_lesson_access.py", "")
sys.path.insert(0, ROOT)
os.environ["JTUTOR_ROOT"] = ROOT

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import backend.app.db as db_mod
from backend.app.lesson_access import locked_response
from backend.app.db import init_db

_tmp = tempfile.mkdtemp()
db_mod.engine = create_engine(f"sqlite:///{_tmp}/t.db", echo=False)
db_mod.SessionLocal = sessionmaker(bind=db_mod.engine, autoflush=False, autocommit=False)
init_db()


def test_locked_lesson_l05():
    db = db_mod.SessionLocal()
    try:
        assert locked_response(db, "L05") is not None
        assert locked_response(db, "L05")["locked"] is True
        assert locked_response(db, "L01") is None
    finally:
        db.close()
