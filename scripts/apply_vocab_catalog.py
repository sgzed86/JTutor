"""Apply curated per-word vocab lists to Starter lesson YAML (surgical edits)."""

from __future__ import annotations

import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from vocab_catalog_starter import (  # noqa: E402
    GLOSSES,
    LESSON_VOCAB_EXTRA,
    REPEAT_PHRASES,
    VOCAB_WORDS,
)


def _q(text: str) -> str:
    text = str(text)
    if any(ch in text for ch in ":#{}[],&*!|>%@`'\"\n") or text[:1] in "-?" or text.isdigit():
        return yaml.dump(text, allow_unicode=True, default_style='"').strip()
    return text


def dump_phrases(words: list[str]) -> str:
    lines = ["  key_phrases:"]
    for w in words:
        lines.append(f"  - {_q(w)}")
    return "\n".join(lines) + "\n"


def dump_meta(words: list[str]) -> str:
    lines = ["  phrase_meta:"]
    for w in words:
        lines.append(f"  - jp: {_q(w)}")
        lines.append("    tags:")
        lines.append("    - short" if len(w) <= 8 else "    - long")
        if w.endswith(("です", "ます", "か", "？", "?")):
            lines.append("    - polite")
    return "\n".join(lines) + "\n"


def dump_glosses(words: list[str]) -> str:
    pairs = [(w, GLOSSES[w]) for w in words if w in GLOSSES]
    if not pairs:
        return ""
    lines = ["  glosses_en:"]
    for w, g in pairs:
        lines.append(f"    {_q(w)}: {_q(g)}")
    return "\n".join(lines) + "\n"


def patch_activity(text: str, act_id: str, words: list[str], *, promote_repeat_all: bool = False) -> str:
    m = re.search(rf"(?m)^- id: {re.escape(act_id)}\s*$", text)
    if not m:
        raise KeyError(act_id)
    start = m.start()
    rest = text[start + 1 :]
    nxt = re.search(r"(?m)^- id: ", rest)
    end = start + 1 + (nxt.start() if nxt else len(rest))
    chunk = text[start:end]

    # Replace key_phrases block
    chunk = re.sub(r"(?ms)^  key_phrases:.*?(?=^  [a-z_]+:|\Z)", dump_phrases(words), chunk, count=1)
    if re.search(r"(?m)^  phrase_meta:", chunk):
        chunk = re.sub(r"(?ms)^  phrase_meta:.*?(?=^  [a-z_]+:|\Z)", dump_meta(words), chunk, count=1)
    else:
        chunk = chunk.rstrip() + "\n" + dump_meta(words)

    gloss_block = dump_glosses(words)
    if gloss_block:
        if re.search(r"(?m)^  glosses_en:", chunk):
            chunk = re.sub(r"(?ms)^  glosses_en:.*?(?=^  [a-z_]+:|\Z)", gloss_block, chunk, count=1)
        else:
            chunk = chunk.rstrip() + "\n" + gloss_block

    # Ensure vocab_drill / pronunciation keep sensible prompt
    if re.search(r"(?m)^  book_mode: vocab_drill", chunk):
        chunk = re.sub(
            r"(?m)^  prompt_en:.*$",
            f"  prompt_en: Listen to the CD, then say each word one at a time ({len(words)} words).",
            chunk,
            count=1,
        )
    # Split mashed listen_repeat into one phrase per step
    if promote_repeat_all and re.search(r"(?m)^  book_mode: listen_repeat\s*$", chunk):
        chunk = re.sub(
            r"(?m)^  book_mode: listen_repeat\s*$",
            "  book_mode: listen_repeat_all",
            chunk,
            count=1,
        )
        chunk = re.sub(
            r"(?m)^  prompt_en:.*$",
            f"  prompt_en: Listen, then repeat each line one at a time ({len(words)} lines).",
            chunk,
            count=1,
        )
    if not chunk.endswith("\n"):
        chunk += "\n"
    return text[:start] + chunk + text[end:]


def looks_concatenated(phrases: list[str]) -> bool:
    if len(phrases) == 1 and len(phrases[0]) >= 25:
        return True
    return any(len(p) >= 40 and "。" not in p and "、" not in p for p in phrases)


_SENTENCE_MARKERS = (
    "です",
    "ます",
    "ください",
    "お願いします",
    "あります",
    "います",
    "行きます",
    "乗ります",
    "？",
    "?",
)


def _is_lemma(word: str) -> bool:
    w = word.strip()
    if not w or len(w) > 18:
        return False
    if any(m in w for m in _SENTENCE_MARKERS) and len(w) > 6:
        return False
    if "、" in w:
        return False
    return True


def dump_lesson_vocab(lesson_id: str, words: list[str]) -> str:
    lines = ["vocab:"]
    for w in words:
        lines.append(f"- jp: {_q(w)}")
        lines.append("  reading: ''")
        en = GLOSSES.get(w, "")
        lines.append(f"  en: {_q(en)}" if en else "  en: ''")
        lines.append("  tags:")
        lines.append(f"  - {lesson_id}")
    return "\n".join(lines) + "\n"


def patch_lesson_vocab(text: str, lesson_id: str, words: list[str]) -> str:
    block = dump_lesson_vocab(lesson_id, words)
    if re.search(r"(?m)^vocab:\s*$", text):
        return re.sub(r"(?ms)^vocab:\n.*?(?=^[a-z_]+:|\Z)", block, text, count=1)
    # Append before trailing can_dos / end if no vocab section
    return text.rstrip() + "\n\n" + block


def lesson_vocab_words(lesson_id: str) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for (lid, _aid), words in sorted(VOCAB_WORDS.items()):
        if lid != lesson_id:
            continue
        for w in words:
            if not _is_lemma(w) or w in seen:
                continue
            seen.add(w)
            out.append(w)
    for w in LESSON_VOCAB_EXTRA.get(lesson_id, []):
        if w not in seen:
            seen.add(w)
            out.append(w)
    return out


def main() -> int:
    n = 0
    touched: set[str] = set()
    all_items = {**VOCAB_WORDS, **REPEAT_PHRASES}
    for (lid, aid), words in sorted(all_items.items()):
        path = ROOT / "content" / "starter" / f"{lid}.yaml"
        if not path.is_file():
            print("missing", path)
            continue
        text = path.read_text(encoding="utf-8")
        data = yaml.safe_load(text) or {}
        act = next((a for a in data.get("activities") or [] if a.get("id") == aid), None)
        if act is None:
            print(f"skip missing activity {lid} {aid}")
            continue
        old = [p for p in (act.get("key_phrases") or []) if p]
        if old != words:
            text = patch_activity(
                text,
                aid,
                words,
                promote_repeat_all=(lid, aid) in REPEAT_PHRASES,
            )
            path.write_text(text, encoding="utf-8")
            n += 1
            print(f"{lid} {aid}: {len(old)} -> {len(words)} items")
        touched.add(lid)

    # Also touch lessons that only need vocab section cleanup via EXTRA
    touched.update(LESSON_VOCAB_EXTRA.keys())

    v = 0
    for lid in sorted(touched):
        path = ROOT / "content" / "starter" / f"{lid}.yaml"
        words = lesson_vocab_words(lid)
        if not words:
            continue
        text = path.read_text(encoding="utf-8")
        data = yaml.safe_load(text) or {}
        old_v = [str(x.get("jp") or "") for x in (data.get("vocab") or []) if isinstance(x, dict)]
        if old_v == words:
            continue
        if any(looks_concatenated([jp]) for jp in old_v) or len(old_v) != len(words):
            text = patch_lesson_vocab(text, lid, words)
            path.write_text(text, encoding="utf-8")
            v += 1
            print(f"{lid} vocab: {len(old_v)} -> {len(words)} entries")
    print(f"updated {n} activities, {v} lesson vocab sections")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
