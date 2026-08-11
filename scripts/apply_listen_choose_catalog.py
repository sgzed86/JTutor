"""Apply curated listen_choose catalog + mild leading-track-number cleanup."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from apply_vocab_catalog import _q, dump_meta, dump_phrases  # noqa: E402
from listen_choose_catalog_starter import LISTEN_CHOOSE as STARTER_CHOOSE  # noqa: E402
from listen_choose_catalog_elementary1 import LISTEN_CHOOSE as EL_CHOOSE  # noqa: E402

# Combined catalog; lesson id prefix selects book.
LISTEN_CHOOSE: dict[tuple[str, str], dict] = {**STARTER_CHOOSE, **EL_CHOOSE}


def book_for(lesson_id: str) -> str:
    return "elementary1" if lesson_id.startswith("EL") else "starter"

# Leading CD/track numbers glued onto otherwise readable Japanese.
# Keep in sync with scripts/_audit_bad_choices.py.
_LEADING_TRACK = re.compile(
    r"^(?:"
    r"[0-9]{1,2}(?=[\u3040-\u30ff\u4e00-\u9fff])(?![年人日月時分番個目度円ヶカかこ戸階回])"
    r"|よん(?=[\u3040-\u30ff\u4e00-\u9fff])"
    r"|[一二三四](?![年人日月時分番個目度円ヶカかこ戸階回緒季])"
    r")"
)


def activity_chunk(text: str, act_id: str) -> tuple[int, int, str]:
    m = re.search(rf"(?m)^- id: {re.escape(act_id)}\s*$", text)
    if not m:
        raise KeyError(act_id)
    start = m.start()
    rest = text[start + 1 :]
    nxt = re.search(r"(?m)^- id: ", rest)
    end = start + 1 + (nxt.start() if nxt else len(rest))
    return start, end, text[start:end]


def dump_choices(choices: list[dict]) -> str:
    lines = ["  choices:"]
    for c in choices:
        lines.append(f"  - id: {c['id']}")
        lines.append(f"    label_jp: {_q(c['label_jp'])}")
        if c.get("label_en"):
            lines.append(f"    label_en: {_q(c['label_en'])}")
    return "\n".join(lines) + "\n"


def dump_correct_ids(ids: list[str]) -> str:
    lines = ["  correct_ids:"]
    for i in ids:
        lines.append(f"  - {i}")
    return "\n".join(lines) + "\n"


def set_line(chunk: str, key: str, value: str) -> str:
    line = f"  {key}: {_q(value)}"
    if re.search(rf"(?m)^  {re.escape(key)}:", chunk):
        return re.sub(rf"(?m)^  {re.escape(key)}:.*$", line, chunk, count=1)
    # insert before book_mode if possible
    if re.search(r"(?m)^  book_mode:", chunk):
        return re.sub(r"(?m)^  book_mode:", line + "\n  book_mode:", chunk, count=1)
    return chunk.rstrip() + "\n" + line + "\n"


def apply_catalog_entry(text: str, act_id: str, entry: dict) -> str:
    start, end, chunk = activity_chunk(text, act_id)
    phrases = list(entry["key_phrases"])
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
        # insert after key_phrases
        chunk = re.sub(
            r"(?ms)(^  key_phrases:.*?)(?=^  [a-z_]+:)",
            lambda m: m.group(1).rstrip() + "\n" + dump_meta(phrases),
            chunk,
            count=1,
        )

    chunk = set_line(chunk, "prompt_en", entry["prompt_en"])
    if entry.get("picture_hint_en"):
        chunk = set_line(chunk, "picture_hint_en", entry["picture_hint_en"])

    chunk = re.sub(
        r"(?ms)^  choices:.*?(?=^  [a-z_]+:|\Z)",
        dump_choices(entry["choices"]),
        chunk,
        count=1,
    )
    chunk = re.sub(
        r"(?ms)^  correct_ids:.*?(?=^  [a-z_]+:|\Z)",
        dump_correct_ids(entry["correct_ids"]),
        chunk,
        count=1,
    )
    mode = entry.get("choose_mode") or "any"
    if re.search(r"(?m)^  choose_mode:", chunk):
        chunk = re.sub(r"(?m)^  choose_mode:.*$", f"  choose_mode: {mode}", chunk, count=1)
    else:
        chunk = chunk.rstrip() + f"\n  choose_mode: {mode}\n"

    if not chunk.endswith("\n"):
        chunk += "\n"
    return text[:start] + chunk + text[end:]


def strip_leading_track(label: str) -> str:
    s = (label or "").strip()
    m = _LEADING_TRACK.match(s)
    if not m:
        return s
    rest = s[m.end() :].lstrip(" 　・.．")
    # Only strip when remainder looks like real Japanese (not empty / tiny)
    if len(rest) < 4:
        return s
    return rest


def mild_clean_chunk(chunk: str) -> tuple[str, int]:
    """Strip leading track numbers from key_phrases / choice labels in one activity."""
    n = 0

    def fix_phrases_block(bm: re.Match) -> str:
        nonlocal n
        block = bm.group(0)
        lines = []
        for line in block.splitlines(keepends=True):
            pm = re.match(r"^(  - )(.+)$", line.rstrip("\n"))
            if pm and not line.strip().startswith("- id:"):
                raw = pm.group(2).strip()
                val = raw
                if (val.startswith('"') and val.endswith('"')) or (val.startswith("'") and val.endswith("'")):
                    try:
                        val = yaml.safe_load(val)
                    except Exception:
                        val = val.strip("\"'")
                if isinstance(val, str):
                    cleaned = strip_leading_track(val)
                    if cleaned != val:
                        n += 1
                        lines.append(f"  - {_q(cleaned)}\n")
                        continue
            lines.append(line if line.endswith("\n") else line + "\n")
        return "".join(lines)

    chunk2 = re.sub(
        r"(?ms)^  key_phrases:.*?(?=^  [a-z_]+:|\Z)",
        fix_phrases_block,
        chunk,
        count=1,
    )

    # choice label_jp lines
    def fix_label(m: re.Match) -> str:
        nonlocal n
        raw = m.group(1)
        try:
            val = yaml.safe_load(raw)
        except Exception:
            val = raw.strip().strip("\"'")
        if not isinstance(val, str):
            return m.group(0)
        cleaned = strip_leading_track(val)
        if cleaned != val:
            n += 1
            return f"    label_jp: {_q(cleaned)}"
        return m.group(0)

    chunk2 = re.sub(r"(?m)^    label_jp: (.+)$", fix_label, chunk2)

    # sync phrase_meta jp lines that still have leading numbers
    def fix_meta_jp(m: re.Match) -> str:
        nonlocal n
        raw = m.group(1)
        try:
            val = yaml.safe_load(raw)
        except Exception:
            val = raw.strip().strip("\"'")
        if not isinstance(val, str):
            return m.group(0)
        cleaned = strip_leading_track(val)
        if cleaned != val:
            n += 1
            return f"  - jp: {_q(cleaned)}"
        return m.group(0)

    chunk2 = re.sub(r"(?m)^  - jp: (.+)$", fix_meta_jp, chunk2)
    return chunk2, n


def mild_clean_file(text: str, catalog_ids: set[str]) -> tuple[str, int]:
    total = 0
    # find all listen_choose activities not in catalog
    ids = re.findall(r"(?m)^- id: (\w+)\s*$", text)
    for act_id in ids:
        if act_id in catalog_ids:
            continue
        try:
            start, end, chunk = activity_chunk(text, act_id)
        except KeyError:
            continue
        if "book_mode: listen_choose" not in chunk:
            continue
        new_chunk, n = mild_clean_chunk(chunk)
        if n:
            text = text[:start] + new_chunk + text[end:]
            total += n
    return text, total


def update_transcripts() -> int:
    total = 0
    by_book: dict[str, dict] = {}
    for (lid, aid), entry in LISTEN_CHOOSE.items():
        tr = entry.get("transcript")
        if not tr:
            continue
        book = book_for(lid)
        if book not in by_book:
            path = ROOT / "content" / book / "audio_transcripts.json"
            by_book[book] = {
                "path": path,
                "data": json.loads(path.read_text(encoding="utf-8")),
                "n": 0,
            }
        ypath = ROOT / "content" / book / f"{lid}.yaml"
        ydata = yaml.safe_load(ypath.read_text(encoding="utf-8"))
        act = next((a for a in ydata.get("activities") or [] if a.get("id") == aid), None)
        if not act:
            continue
        audio = (act.get("audio") or [None])[0]
        if not audio:
            continue
        bucket = by_book[book]
        if bucket["data"].get(audio) != tr:
            bucket["data"][audio] = tr
            bucket["n"] += 1
    for bucket in by_book.values():
        if bucket["n"]:
            bucket["path"].write_text(
                json.dumps(bucket["data"], ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            total += bucket["n"]
    return total


def main() -> int:
    by_lesson: dict[str, list[str]] = {}
    for lid, aid in LISTEN_CHOOSE:
        by_lesson.setdefault(lid, []).append(aid)

    for lid, aids in sorted(by_lesson.items()):
        book = book_for(lid)
        path = ROOT / "content" / book / f"{lid}.yaml"
        text = path.read_text(encoding="utf-8")
        catalog_ids = set(aids)
        for aid in aids:
            entry = LISTEN_CHOOSE[(lid, aid)]
            text = apply_catalog_entry(text, aid, entry)
            print(f"catalog {lid} {aid}")
        text, mild_n = mild_clean_file(text, catalog_ids)
        if mild_n:
            print(f"  mild-stripped {mild_n} labels/phrases in {lid}")
        path.write_text(text, encoding="utf-8")

    # mild-clean remaining starter + elementary1 lessons with no catalog entries
    catalog_lessons = set(by_lesson)
    for book in ("starter", "elementary1"):
        pattern = "L*.yaml" if book == "starter" else "EL*.yaml"
        for path in sorted((ROOT / "content" / book).glob(pattern)):
            if path.stem in catalog_lessons:
                # already mild-cleaned above for non-catalog acts in that file
                continue
            text = path.read_text(encoding="utf-8")
            text2, mild_n = mild_clean_file(text, set())
            if mild_n:
                path.write_text(text2, encoding="utf-8")
                print(f"mild {path.stem}: stripped {mild_n}")

    n_tr = update_transcripts()
    print(f"transcripts updated: {n_tr}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
