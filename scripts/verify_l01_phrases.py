#!/usr/bin/env python3
"""Print L01 activity → expected phrase (for cross-check with book CD)."""
from __future__ import annotations

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
L01 = ROOT / "content" / "starter" / "L01.yaml"


def main() -> None:
    data = yaml.safe_load(L01.read_text(encoding="utf-8"))
    missing = []
    for a in data["activities"]:
        if a.get("kind") == "script":
            continue
        if not a.get("key_phrases"):
            missing.append(a["book_activity"])
    print("Missing key_phrases (non-script):", missing or "none")
    print()
    for a in data["activities"]:
        if a.get("kind") == "script":
            continue
        n = a["book_activity"]
        fn = (a.get("audio") or [""])[0].rsplit("/", 1)[-1]
        phrase = (a.get("key_phrases") or [""])[0]
        print(f"  {n:2d}  {fn:32s}  {phrase}")


if __name__ == "__main__":
    main()
