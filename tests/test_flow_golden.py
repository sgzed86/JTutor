"""Whole-lesson progression is pinned to recorded golden transcripts.

Regenerate deliberately (and review the diff) with:

    JTUTOR_REGEN_GOLDENS=1 pytest tests/test_flow_golden.py
"""

from __future__ import annotations

import os

import pytest

from tests.flow_harness import read_golden, run_lesson, write_golden

REGEN = os.environ.get("JTUTOR_REGEN_GOLDENS") == "1"


def _all_lesson_ids() -> list[str]:
    from backend.app.curriculum_loader import list_lessons

    ids: list[str] = []
    for book in ("starter", "elementary1"):
        ids.extend(str(x["lesson_id"]) for x in list_lessons(book))
    return ids


LESSON_IDS = _all_lesson_ids()


def test_every_lesson_is_covered():
    assert len(LESSON_IDS) == 37, LESSON_IDS


@pytest.mark.parametrize("lesson_id", LESSON_IDS)
def test_lesson_transcript_matches_golden(lesson_id, clean_db, no_llm):
    trace = run_lesson(lesson_id)

    if REGEN:
        write_golden(lesson_id, trace)
        pytest.skip(f"regenerated golden for {lesson_id}")

    golden = read_golden(lesson_id)
    assert golden, f"missing golden for {lesson_id} — run with JTUTOR_REGEN_GOLDENS=1"
    assert len(trace) == len(golden), (
        f"{lesson_id}: {len(trace)} steps vs {len(golden)} in golden"
    )
    for i, (got, want) in enumerate(zip(trace, golden, strict=True)):
        assert got == want, f"{lesson_id} diverges at step {i}:\n got={got}\nwant={want}"


@pytest.mark.parametrize("lesson_id", ["L01", "L05", "EL01"])
def test_lesson_terminates(lesson_id, clean_db, no_llm):
    trace = run_lesson(lesson_id)
    assert trace[-1].get("action") != "ABORTED_MAX_TURNS"
    assert trace[-1]["state"] == "lesson_complete"


def test_progress_never_goes_backwards(clean_db, no_llm):
    trace = run_lesson("L02")
    seen = [row["progress_pct"] for row in trace if row.get("progress_pct") is not None]
    assert seen == sorted(seen), "lesson progress percentage decreased mid-lesson"
    assert seen[-1] == 100
