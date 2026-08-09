#!/usr/bin/env python3
"""Validate generated lesson YAML (phrase quality gates)."""

from __future__ import annotations

import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
MAX_PHRASE_LEN = 25
LATIN_RUN = re.compile(r"[A-Za-z]{4,}")
DIGIT_START = re.compile(r"^[0-9０-９]")


def validate_lesson(path: Path) -> list[str]:
    errors: list[str] = []
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    lid = data.get("lesson_id") or path.stem
    for a in data.get("activities") or []:
        aid = a.get("id")
        for p in a.get("key_phrases") or []:
            s = str(p).strip()
            if not s:
                continue
            if len(s) > MAX_PHRASE_LEN:
                errors.append(f"{lid} {aid}: phrase too long ({len(s)}): {s[:40]}…")
            if DIGIT_START.match(s):
                errors.append(f"{lid} {aid}: phrase starts with digit: {s[:30]}")
            if LATIN_RUN.search(s):
                errors.append(f"{lid} {aid}: latin garbage in phrase: {s[:40]}")
    return errors


def main() -> None:
    strict = "--strict" in sys.argv
    all_errors: list[str] = []
    for sub in ("starter", "elementary1"):
        d = ROOT / "content" / sub
        if not d.is_dir():
            continue
        for path in sorted(d.glob("*.yaml")):
            if "phrase_reference" in path.name or path.name == "index.yaml":
                continue
            all_errors.extend(validate_lesson(path))

    if all_errors:
        print(f"Found {len(all_errors)} phrase issues:")
        for e in all_errors[:80]:
            print(" ", e)
        if len(all_errors) > 80:
            print(f"  … and {len(all_errors) - 80} more")
        if strict:
            raise SystemExit(1)
        print("\nRe-run with --strict to fail the build.")
        return
    print("No phrase validation issues found.")


if __name__ == "__main__":
    main()
