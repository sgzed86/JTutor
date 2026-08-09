#!/usr/bin/env python3
"""Build Elementary 1 content pipeline (audio index → PDF → grammar → curriculum)."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = [
    ["index_audio.py", "--book", "elementary1"],
    ["extract_pdf_elementary1.py"],
    ["extract_grammar_elementary1.py"],
    ["extract_scripts_elementary1.py"],  # phrases from textbook scripts (no Whisper)
    ["build_curriculum_elementary1.py"],
]


def main() -> None:
    for args in SCRIPTS:
        path = ROOT / "scripts" / args[0]
        cmd = [sys.executable, str(path), *args[1:]]
        print(f"\n=== {' '.join(args)} ===")
        r = subprocess.run(cmd, cwd=str(ROOT))
        if r.returncode != 0:
            raise SystemExit(r.returncode)
    print("\nElementary 1 curriculum build complete.")
    print("Phrases come from PDF dialog scripts — Whisper is not required.")


if __name__ == "__main__":
    main()
