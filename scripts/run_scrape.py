#!/usr/bin/env python3
"""Run the full content scrape pipeline."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = [
    "index_audio.py",
    "extract_pdf.py",
    "extract_grammar.py",
    "build_curriculum.py",
]


def main() -> None:
    for name in SCRIPTS:
        path = ROOT / "scripts" / name
        print(f"\n=== {name} ===")
        r = subprocess.run([sys.executable, str(path)], cwd=str(ROOT))
        if r.returncode != 0:
            raise SystemExit(r.returncode)
    print("\nCurriculum build complete.")


if __name__ == "__main__":
    main()
