"""Deterministic tutor flow snapshots (no voice/ollama)."""

from __future__ import annotations

import asyncio
import os
import sys
import tempfile

import pytest

ROOT = __file__.replace("/tests/test_flow_snapshots.py", "")
sys.path.insert(0, ROOT)
os.environ["JTUTOR_ROOT"] = ROOT

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import backend.app.db as db_mod
from backend.app import orchestrator
from backend.app.db import init_db
from backend.app.book_modes import flow_substeps

_tmp = tempfile.mkdtemp()
db_mod.engine = create_engine(f"sqlite:///{_tmp}/flow.db", echo=False)
db_mod.SessionLocal = sessionmaker(bind=db_mod.engine, autoflush=False, autocommit=False)
init_db()


def _book_substep_sequence(lesson_id: str) -> list[str]:
    from backend.app.curriculum_loader import load_lesson

    lesson = load_lesson(lesson_id)
    seq: list[str] = []
    for act in lesson.get("activities") or []:
        if act.get("kind") in ("script",) and lesson_id != "L00":
            continue
        if act.get("book_skip"):
            continue
        mode = act.get("book_mode") or "listen_repeat"
        subs = flow_substeps(act)
        for s in subs:
            seq.append(f"{act.get('id')}:{mode}:{s}")
    return seq


def test_l01_substep_sequence_stable():
    a = _book_substep_sequence("L01")
    b = _book_substep_sequence("L01")
    assert a == b
    assert "listen" in "".join(a)
    assert len(a) >= 4


def test_l00_includes_classroom_tracks():
    from backend.app import lesson_flow as flow
    from backend.app.curriculum_loader import load_lesson

    lesson = load_lesson("L00")
    tracks = flow.book_tracks(lesson)
    assert len(tracks) >= 1
    assert any(t.get("kind") == "classroom" for t in tracks)


def test_unlock_l05_blocked():
    db = db_mod.SessionLocal()
    try:
        from backend.app.lesson_access import locked_response

        assert locked_response(db, "L05") is not None
    finally:
        db.close()


@pytest.mark.asyncio
async def test_l01_advance_intro_to_book():
    db = db_mod.SessionLocal()
    try:
        out = await orchestrator.start_or_resume(db, "L01")
        assert out.get("lesson_id") == "L01"
        assert out.get("state") in ("lesson_intro", "book", "intro_chat")
        nxt = await orchestrator.advance(db, "L01")
        assert nxt.get("state") != "lesson_intro"
    finally:
        db.close()
