"""Tutor mode protocol (Tier 3.1 foundation — dispatch not migrated yet)."""

from __future__ import annotations

from typing import Any, Mapping, Protocol, Sequence


class TutorMode(Protocol):
    name: str

    def substeps(self, activity: Mapping[str, Any]) -> Sequence[str]: ...

    def expected(self, activity: Mapping[str, Any], index: int) -> list[str]: ...
