"""Deterministic driver used to record and replay whole-lesson transcripts.

The point of this harness is to pin *progression*: for a fixed sequence of
learner actions, every lesson must walk exactly the same states, activities,
sub-steps and scripted lines. Any refactor of the orchestrator or the lesson
flow has to reproduce these traces byte for byte.
"""

from __future__ import annotations

import asyncio
import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

GOLDEN_DIR = Path(__file__).parent / "golden"
MAX_TURNS = 900


def _answer_for(payload: dict[str, Any]) -> str:
    """What a learner who always answers correctly would say at this step."""
    step = payload.get("step") or {}
    if payload.get("state") == "grammar":
        expected = step.get("expected_phrases") or []
        if expected:
            return str(expected[0])
        grammar_pts = payload.get("grammar") or []
        idx = min(int(payload.get("quiz_index") or 0), max(len(grammar_pts) - 1, 0))
        if grammar_pts:
            point = grammar_pts[idx]
            for ex in point.get("examples") or []:
                if isinstance(ex, dict) and ex.get("jp"):
                    return str(ex["jp"])
                if isinstance(ex, str) and ex.strip():
                    return str(ex)
            if point.get("point"):
                return str(point["point"])[:80]
    target = step.get("say_target_jp")
    if target:
        return str(target)
    expected = step.get("expected_phrases") or step.get("say_alternates_jp") or []
    if expected:
        return str(expected[0])
    line = step.get("dialog_line_jp")
    if line:
        return str(line)

    # Can-do checks without a scripted scenario grade against the rubric.
    can_do_id = step.get("can_do_id")
    if can_do_id:
        for cd in payload.get("can_dos") or []:
            if cd.get("id") == can_do_id:
                must = (cd.get("rubric") or {}).get("must_include") or []
                if must:
                    return str(must[0])
    if payload.get("state") == "can_do_quiz":
        idx = int(payload.get("quiz_index") or 0)
        can_dos = payload.get("can_dos") or []
        if idx < len(can_dos):
            must = (can_dos[idx].get("rubric") or {}).get("must_include") or []
            if must:
                return str(must[0])

    activity = payload.get("activity") or {}
    phrases = activity.get("key_phrases") or []
    if phrases:
        return str(phrases[0])
    return "はい"


def _trace_row(action: str, payload: dict[str, Any]) -> dict[str, Any]:
    step = payload.get("step") or {}
    messages = payload.get("messages") or []
    last_assistant = ""
    for m in reversed(messages):
        if m.get("role") == "assistant":
            last_assistant = m.get("content") or ""
            break
    progress = payload.get("progress") or {}
    return {
        "action": action,
        "state": payload.get("state"),
        "activity_id": payload.get("activity_id"),
        "quiz_index": payload.get("quiz_index"),
        "phase": step.get("phase"),
        "substep": step.get("book_substep"),
        "book_mode": step.get("book_mode"),
        "expect_speech": bool(step.get("expect_speech")),
        "auto_advance": bool(step.get("auto_advance_after_audio")),
        "audio": len(step.get("play_audio") or []),
        "say_target": step.get("say_target_jp"),
        "tutor_jp": last_assistant,
        "progress_pct": progress.get("percent"),
    }


def _position(payload: dict[str, Any]) -> tuple[Any, ...]:
    step = payload.get("step") or {}
    return (
        payload.get("state"),
        payload.get("activity_id"),
        payload.get("quiz_index"),
        step.get("book_substep"),
    )


async def _run_async(
    lesson_id: str,
    *,
    answer: Callable[[dict[str, Any]], str] = _answer_for,
) -> list[dict[str, Any]]:
    from backend.app import orchestrator
    from backend.app.db import LessonProgress, SessionLocal

    trace: list[dict[str, Any]] = []
    with SessionLocal() as db:
        row = db.get(LessonProgress, lesson_id)
        if row is None:
            db.add(LessonProgress(lesson_id=lesson_id, unlocked=True))
        else:
            row.unlocked = True
        db.commit()

        payload = await orchestrator.start_or_resume(db, lesson_id)
        trace.append(_trace_row("start", payload))

        stuck_at: tuple[Any, ...] | None = None
        stuck_count = 0
        for _ in range(MAX_TURNS):
            state = payload.get("state")
            if state == "lesson_complete":
                break
            step = payload.get("step") or {}

            here = _position(payload)
            if here == stuck_at:
                stuck_count += 1
                if stuck_count > 3:
                    trace.append({"action": "STUCK", "at": list(here)})
                    break
            else:
                stuck_at, stuck_count = here, 0

            if state == "self_check":
                can_do_id = (payload.get("self_check") or {}).get("can_do_id") or step.get("can_do_id")
                if can_do_id:
                    payload = await orchestrator.submit_self_check(
                        db, lesson_id, can_do_id=can_do_id, stars=2, comment=""
                    )
                    trace.append(_trace_row("self_check", payload))
                    continue
                payload = await orchestrator.advance(db, lesson_id)
                trace.append(_trace_row("advance", payload))
                continue

            if step.get("expect_speech"):
                text = answer(payload)
                payload = await orchestrator.user_message(db, lesson_id, text, spoken=True)
                trace.append(_trace_row(f"say:{text}", payload))
                continue

            payload = await orchestrator.advance(db, lesson_id)
            trace.append(_trace_row("advance", payload))
        else:  # pragma: no cover - guard against a non-terminating flow
            trace.append({"action": "ABORTED_MAX_TURNS"})
    return trace


def run_lesson(lesson_id: str, **kwargs: Any) -> list[dict[str, Any]]:
    return asyncio.run(_run_async(lesson_id, **kwargs))


def golden_path(lesson_id: str) -> Path:
    return GOLDEN_DIR / f"{lesson_id}.jsonl"


def write_golden(lesson_id: str, trace: list[dict[str, Any]]) -> None:
    GOLDEN_DIR.mkdir(parents=True, exist_ok=True)
    with golden_path(lesson_id).open("w", encoding="utf-8") as fh:
        for row in trace:
            fh.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def read_golden(lesson_id: str) -> list[dict[str, Any]]:
    path = golden_path(lesson_id)
    if not path.is_file():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
