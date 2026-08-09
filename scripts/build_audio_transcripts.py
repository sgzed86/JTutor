#!/usr/bin/env python3
"""Transcribe Irodori MP3s → content/starter/audio_transcripts.json (cached)."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AUDIO_INDEX = ROOT / "content" / "starter" / "audio_index.json"
OUT = ROOT / "content" / "starter" / "audio_transcripts.json"
ASSETS = ROOT / "assets" / "audio"


def main() -> None:
    import whisper

    audio = json.loads(AUDIO_INDEX.read_text(encoding="utf-8"))
    cache: dict[str, str] = {}
    if OUT.exists():
        cache = json.loads(OUT.read_text(encoding="utf-8"))

    model_name = "tiny"
    if len(sys.argv) > 1:
        model_name = sys.argv[1]
    print(f"Loading Whisper {model_name}...")
    model = whisper.load_model(model_name)

    todo: list[tuple[str, Path]] = []
    for t in audio.get("tracks") or []:
        rel = t.get("rel_path") or ""
        if not rel.endswith(".mp3"):
            continue
        if rel in cache and cache[rel].strip():
            continue
        path = ROOT / rel.replace("/", "\\") if "\\" in str(ROOT) else ROOT / rel
        if not path.is_file():
            path = ASSETS / Path(rel).name
        if not path.is_file():
            print("MISSING", rel)
            continue
        todo.append((rel, path))

    print(f"Transcribing {len(todo)} files ({len(cache)} cached)...")
    for i, (rel, path) in enumerate(todo, 1):
        print(f"[{i}/{len(todo)}] {path.name}")
        r = model.transcribe(str(path), language="ja", fp16=False)
        text = re.sub(r"\s+", " ", (r.get("text") or "").strip())
        cache[rel] = text
        if i % 25 == 0:
            OUT.write_text(json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8")

    OUT.write_text(json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {OUT} ({len(cache)} entries)")


if __name__ == "__main__":
    main()
