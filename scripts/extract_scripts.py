#!/usr/bin/env python3
"""Run PDF script extraction for starter or elementary1."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BOOKS = {
    "starter": "extract_scripts_starter.py",
    "elementary1": "extract_scripts_elementary1.py",
}


def main() -> None:
    book = (sys.argv[1] if len(sys.argv) > 1 else "starter").strip()
    script = BOOKS.get(book)
    if not script:
        raise SystemExit(f"Unknown book {book!r}. Choose: {', '.join(BOOKS)}")
    path = ROOT / "scripts" / script
    raise SystemExit(subprocess.call([sys.executable, str(path)], cwd=str(ROOT)))


if __name__ == "__main__":
    main()
