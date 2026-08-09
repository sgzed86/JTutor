"""Tutor mode registry (Tier 3.1) — dispatches book_step by book_mode."""

from __future__ import annotations

from typing import Any, Callable

from backend.app import lesson_flow as flow
from backend.app.book_modes import book_mode

RenderFn = Callable[[dict, dict, int], tuple[str, str, dict]]


class _DelegatedMode:
    def __init__(self, name: str):
        self.name = name

    def render(self, activity: dict, lesson: dict, index: int) -> tuple[str, str, dict]:
        return flow.book_step(activity, lesson, index)


_MODES: dict[str, _DelegatedMode] = {}


def _ensure_modes() -> None:
    if _MODES:
        return
    from backend.app.book_modes import FLOW_BY_MODE

    for mode_name in FLOW_BY_MODE:
        _MODES[mode_name] = _DelegatedMode(mode_name)
    for extra in ("repeat",):
        _MODES.setdefault(extra, _DelegatedMode(extra))


def render_book_step(activity: dict, lesson: dict, index: int) -> tuple[str, str, dict]:
    _ensure_modes()
    return flow.book_step(activity, lesson, index)
