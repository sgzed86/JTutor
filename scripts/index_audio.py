#!/usr/bin/env python3
"""Index Irodori MP3 files from assets/audio into content/<book>/audio_index.json."""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from books import BOOKS, get_book  # noqa: E402

AUDIO_DIR = ROOT / "assets" / "audio"

KIND_MAP = {
    "kiku": "listening",
    "hanasu": "speaking",
    "katachi": "grammar_form",
    "kaiwa": "conversation",
    "kotoba": "vocabulary",
    "hiragana": "hiragana",
    "katakana": "katakana",
    "kyoshitsu": "classroom",
    "yomu": "reading",
}


def classify(label: str) -> tuple[str, str]:
    clean = label.strip().lower().replace(" ", "")
    base = re.split(r"[\d_\-]", clean, maxsplit=1)[0]
    kind = KIND_MAP.get(base, base or "other")
    return kind, clean


def index_book(book_id: str) -> None:
    book = get_book(book_id)
    prefix = book.audio_prefix  # X_ or Y_
    pattern = re.compile(
        rf"^{re.escape(prefix)}\[(?P<lesson>\d{{2}})-(?P<track>\d{{2}})\]_(?P<label>.+)\.mp3$",
        re.IGNORECASE,
    )
    if not AUDIO_DIR.is_dir():
        raise SystemExit(f"Audio directory not found: {AUDIO_DIR}")

    tracks: list[dict] = []
    by_lesson: dict[str, list[dict]] = defaultdict(list)
    lid_prefix = book.lesson_id_prefix

    for path in sorted(AUDIO_DIR.glob(f"{prefix}*.mp3")):
        m = pattern.match(path.name)
        if not m:
            print(f"skip unrecognized: {path.name}")
            continue
        lesson = int(m.group("lesson"))
        track = int(m.group("track"))
        label = m.group("label")
        kind, subtype = classify(label)
        lesson_id = f"{lid_prefix}{lesson:02d}"
        entry = {
            "filename": path.name,
            "rel_path": f"assets/audio/{path.name}",
            "lesson": lesson,
            "lesson_id": lesson_id,
            "track": track,
            "label": label.strip(),
            "kind": kind,
            "subtype": subtype,
            "book_id": book.id,
        }
        tracks.append(entry)
        by_lesson[lesson_id].append(entry)

    out = book.content_dir / "audio_index.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "source": "assets/audio",
        "book_id": book.id,
        "audio_prefix": prefix,
        "count": len(tracks),
        "tracks": tracks,
        "by_lesson": {
            k: by_lesson[k]
            for k in sorted(by_lesson, key=lambda x: int(re.sub(r"\D", "", x) or "0"))
        },
    }
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Indexed {len(tracks)} tracks ({book.id}) -> {out}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--book", default="starter", choices=list(BOOKS))
    ap.add_argument("--all", action="store_true", help="Index every registered book")
    args = ap.parse_args()
    if args.all:
        for bid in BOOKS:
            index_book(bid)
    else:
        index_book(args.book)


if __name__ == "__main__":
    main()
