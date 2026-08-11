"""Apply curated starter dialog_catalog surgically (no whole-file yaml dump)."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from apply_vocab_catalog import _q, dump_meta, dump_phrases  # noqa: E402
from dialog_catalog_starter import DIALOG  # noqa: E402


def activity_chunk(text: str, act_id: str) -> tuple[int, int, str]:
    m = re.search(rf"(?m)^- id: {re.escape(act_id)}\s*$", text)
    if not m:
        raise KeyError(act_id)
    start = m.start()
    rest = text[start + 1 :]
    nxt = re.search(r"(?m)^- id: ", rest)
    end = start + 1 + (nxt.start() if nxt else len(rest))
    return start, end, text[start:end]


def dump_dialog_script(script: list[dict]) -> str:
    lines = ["  dialog_script:"]
    for turn in script:
        lines.append(f"  - speaker: {turn['speaker']}")
        lines.append(f"    jp: {_q(turn['jp'])}")
    return "\n".join(lines) + "\n"


def set_line(chunk: str, key: str, value: str) -> str:
    line = f"  {key}: {_q(value)}"
    if re.search(rf"(?m)^  {re.escape(key)}:", chunk):
        return re.sub(rf"(?m)^  {re.escape(key)}:.*$", line, chunk, count=1)
    if re.search(r"(?m)^  book_mode:", chunk):
        return re.sub(r"(?m)^  book_mode:", line + "\n  book_mode:", chunk, count=1)
    return chunk.rstrip() + "\n" + line + "\n"


def apply_entry(text: str, act_id: str, entry: dict) -> str:
    start, end, chunk = activity_chunk(text, act_id)
    phrases = list(entry["key_phrases"])

    chunk = re.sub(
        r"(?ms)^  key_phrases:.*?(?=^  [a-z_]+:|\Z)",
        dump_phrases(phrases),
        chunk,
        count=1,
    )

    if re.search(r"(?m)^  dialog_script:", chunk):
        chunk = re.sub(
            r"(?ms)^  dialog_script:.*?(?=^  [a-z_]+:|\Z)",
            dump_dialog_script(entry["dialog_script"]),
            chunk,
            count=1,
        )
    else:
        # insert after book_mode
        if re.search(r"(?m)^  book_mode:", chunk):
            chunk = re.sub(
                r"(?m)^  book_mode:.*$",
                lambda m: m.group(0) + "\n" + dump_dialog_script(entry["dialog_script"]).rstrip(),
                chunk,
                count=1,
            )
        else:
            chunk = chunk.rstrip() + "\n" + dump_dialog_script(entry["dialog_script"])

    if re.search(r"(?m)^  phrase_meta:", chunk):
        chunk = re.sub(
            r"(?ms)^  phrase_meta:.*?(?=^  [a-z_]+:|\Z)",
            dump_meta(phrases),
            chunk,
            count=1,
        )
    else:
        chunk = re.sub(
            r"(?ms)(^  key_phrases:.*?)(?=^  [a-z_]+:)",
            lambda m: m.group(1).rstrip() + "\n" + dump_meta(phrases),
            chunk,
            count=1,
        )

    if entry.get("prompt_en"):
        chunk = set_line(chunk, "prompt_en", entry["prompt_en"])

    if not chunk.endswith("\n"):
        chunk += "\n"
    return text[:start] + chunk + text[end:]


def update_transcripts() -> int:
    path = ROOT / "content" / "starter" / "audio_transcripts.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    n = 0
    for (lid, aid), entry in DIALOG.items():
        tr = entry.get("transcript")
        if not tr:
            continue
        ypath = ROOT / "content" / "starter" / f"{lid}.yaml"
        ydata = yaml.safe_load(ypath.read_text(encoding="utf-8"))
        act = next((a for a in ydata.get("activities") or [] if a.get("id") == aid), None)
        if not act:
            continue
        audio = (act.get("audio") or [None])[0]
        if not audio:
            continue
        if data.get(audio) != tr:
            data[audio] = tr
            n += 1
    if n:
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return n


def main() -> int:
    by_lesson: dict[str, list[str]] = {}
    for lid, aid in DIALOG:
        by_lesson.setdefault(lid, []).append(aid)

    for lid, aids in sorted(by_lesson.items()):
        path = ROOT / "content" / "starter" / f"{lid}.yaml"
        text = path.read_text(encoding="utf-8")
        for aid in aids:
            text = apply_entry(text, aid, DIALOG[(lid, aid)])
            print(f"dialog {lid} {aid}")
        path.write_text(text, encoding="utf-8")

    n_tr = update_transcripts()
    print(f"transcripts updated: {n_tr}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
