"""Apply curated katachi / counting / vocab OCR fixes surgically to YAML + transcripts."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from apply_clean_fill_extracts import dump_blanks  # noqa: E402
from apply_vocab_catalog import dump_meta, dump_phrases, _q  # noqa: E402
from katachi_fix_catalog import FILL, REPEAT_ALL, TRANSCRIPT_FIXES, VOCAB  # noqa: E402


def book_for(lesson_id: str) -> str:
    return "elementary1" if lesson_id.startswith("EL") else "starter"


def lesson_path(lesson_id: str) -> Path:
    return ROOT / "content" / book_for(lesson_id) / f"{lesson_id}.yaml"


def activity_chunk(text: str, act_id: str) -> tuple[int, int, str]:
    m = re.search(rf"(?m)^- id: {re.escape(act_id)}\s*$", text)
    if not m:
        raise KeyError(act_id)
    start = m.start()
    rest = text[start + 1 :]
    nxt = re.search(r"(?m)^- id: ", rest)
    end = start + 1 + (nxt.start() if nxt else len(rest))
    return start, end, text[start:end]


def replace_phrases(chunk: str, phrases: list[str]) -> str:
    chunk = re.sub(
        r"(?ms)^  key_phrases:.*?(?=^  [a-z_]+:|\Z)",
        dump_phrases(phrases),
        chunk,
        count=1,
    )
    if re.search(r"(?m)^  phrase_meta:", chunk):
        chunk = re.sub(
            r"(?ms)^  phrase_meta:.*?(?=^  [a-z_]+:|\Z)",
            dump_meta(phrases),
            chunk,
            count=1,
        )
    else:
        chunk = chunk.rstrip() + "\n" + dump_meta(phrases)
    return chunk


def set_mode(chunk: str, mode: str, prompt_en: str) -> str:
    if re.search(r"(?m)^  book_mode:", chunk):
        chunk = re.sub(r"(?m)^  book_mode:.*$", f"  book_mode: {mode}", chunk, count=1)
    else:
        chunk = chunk.rstrip() + f"\n  book_mode: {mode}\n"
    if re.search(r"(?m)^  prompt_en:", chunk):
        chunk = re.sub(r"(?m)^  prompt_en:.*$", f"  prompt_en: {prompt_en}", chunk, count=1)
    return chunk


def apply_repeat(text: str, act_id: str, phrases: list[str]) -> str:
    start, end, chunk = activity_chunk(text, act_id)
    chunk = replace_phrases(chunk, phrases)
    chunk = set_mode(
        chunk,
        "listen_repeat_all",
        f"Listen, then repeat each item one at a time ({len(phrases)} items).",
    )
    # Remove leftover blanks if any
    chunk = re.sub(r"(?ms)^  blanks:.*?(?=^  [a-z_]+:|\Z)", "", chunk)
    chunk = re.sub(r"(?m)^  fill_pdf_page:.*\n?", "", chunk)
    if not chunk.endswith("\n"):
        chunk += "\n"
    return text[:start] + chunk + text[end:]


def apply_fill(text: str, act_id: str, page: int, blanks: list[dict], phrases: list[str]) -> str:
    start, end, chunk = activity_chunk(text, act_id)
    chunk = replace_phrases(chunk, phrases)
    chunk = set_mode(
        chunk,
        "listen_fill",
        "Listen to the recording and fill in the blanks.",
    )
    chunk = re.sub(r"(?ms)^  blanks:.*?(?=^  [a-z_]+:|\Z)", "", chunk)
    chunk = re.sub(r"(?m)^  fill_pdf_page:.*\n?", "", chunk)
    chunk = chunk.rstrip() + "\n" + dump_blanks(blanks, page)
    if not chunk.endswith("\n"):
        chunk += "\n"
    return text[:start] + chunk + text[end:]


def apply_vocab(text: str, act_id: str, words: list[str]) -> str:
    start, end, chunk = activity_chunk(text, act_id)
    chunk = replace_phrases(chunk, words)
    chunk = set_mode(
        chunk,
        "vocab_drill",
        f"Listen to the CD, then say each word one at a time ({len(words)} words).",
    )
    if not chunk.endswith("\n"):
        chunk += "\n"
    return text[:start] + chunk + text[end:]


def update_transcripts() -> int:
    n = 0
    for book in ("starter", "elementary1"):
        path = ROOT / "content" / book / "audio_transcripts.json"
        if not path.is_file():
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        changed = False
        for key, value in TRANSCRIPT_FIXES.items():
            if key in data and data[key] != value:
                data[key] = value
                changed = True
                n += 1
                _emit(f"transcript {book}: {key}")
        if changed:
            path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return n


def _emit(msg: str) -> None:
    sys.stdout.buffer.write((msg + "\n").encode("utf-8", errors="replace"))


def main() -> int:
    summary: list[str] = []

    for (lid, aid), phrases in sorted(REPEAT_ALL.items()):
        path = lesson_path(lid)
        text = path.read_text(encoding="utf-8")
        data = yaml.safe_load(text) or {}
        act = next((a for a in data.get("activities") or [] if a.get("id") == aid), None)
        if act is None:
            _emit(f"missing {lid} {aid}")
            continue
        before_mode = act.get("book_mode")
        before_n = len([p for p in (act.get("key_phrases") or []) if p])
        text = apply_repeat(text, aid, phrases)
        path.write_text(text, encoding="utf-8")
        line = (
            f"{lid} {aid}: {before_mode} n={before_n} -> listen_repeat_all n={len(phrases)}"
        )
        _emit(line)
        summary.append(line)

    for (lid, aid), (page, blanks, phrases) in sorted(FILL.items()):
        path = lesson_path(lid)
        text = path.read_text(encoding="utf-8")
        data = yaml.safe_load(text) or {}
        act = next((a for a in data.get("activities") or [] if a.get("id") == aid), None)
        if act is None:
            _emit(f"missing {lid} {aid}")
            continue
        before_mode = act.get("book_mode")
        before_n = len([p for p in (act.get("key_phrases") or []) if p])
        before_b = len(act.get("blanks") or [])
        text = apply_fill(text, aid, page, blanks, phrases)
        path.write_text(text, encoding="utf-8")
        line = (
            f"{lid} {aid}: {before_mode} phrases={before_n} blanks={before_b} "
            f"-> listen_fill phrases={len(phrases)} blanks={len(blanks)}"
        )
        _emit(line)
        summary.append(line)

    for (lid, aid), words in sorted(VOCAB.items()):
        path = lesson_path(lid)
        text = path.read_text(encoding="utf-8")
        data = yaml.safe_load(text) or {}
        act = next((a for a in data.get("activities") or [] if a.get("id") == aid), None)
        if act is None:
            _emit(f"missing {lid} {aid}")
            continue
        before_mode = act.get("book_mode")
        before_n = len([p for p in (act.get("key_phrases") or []) if p])
        text = apply_vocab(text, aid, words)
        path.write_text(text, encoding="utf-8")
        line = f"{lid} {aid}: {before_mode} n={before_n} -> vocab_drill n={len(words)}"
        _emit(line)
        summary.append(line)

    tn = update_transcripts()
    _emit(f"updated {len(summary)} activities, {tn} transcripts")
    out = ROOT / "scripts" / "_katachi_fix_summary.txt"
    out.write_text("\n".join(summary) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
