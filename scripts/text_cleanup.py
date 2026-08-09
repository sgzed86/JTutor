#!/usr/bin/env python3
"""Heuristics to reduce furigana / ruby noise from Irodori PDF text extracts."""

from __future__ import annotations

import re
import unicodedata

# Common furigana-only lines (hiragana/katakana short readings)
_RUBY_LINE = re.compile(r"^[\u3040-\u309F\u30A0-\u30FF\u30FC\s]{1,12}$")
_PAGE_NOISE = re.compile(r"©\s*The Japan Foundation.*", re.IGNORECASE)
_WHITESPACE = re.compile(r"[ \t]+")


def is_likely_ruby(line: str) -> bool:
    s = line.strip()
    if not s:
        return False
    if _RUBY_LINE.match(s):
        return True
    # Single kanji reading patterns sometimes land alone
    if len(s) <= 6 and all(
        "HIRAGANA" in unicodedata.name(ch, "") or "KATAKANA" in unicodedata.name(ch, "") or ch.isspace()
        for ch in s
        if not ch.isspace()
    ):
        return True
    return False


def _ends_incomplete_jp(s: str) -> bool:
    """True if line likely continues after a dropped furigana line (…久 + しぶり)."""
    s = s.rstrip()
    if not s:
        return False
    if s[-1] in "。．.!！?？、，,：:）)」」』…〜～":
        return False
    # Ends with kanji / incomplete kana stem
    return bool(re.search(r"[\u4e00-\u9fff\u3040-\u30ff]$", s))


def _starts_jp_continuation(s: str) -> bool:
    s = s.lstrip()
    if not s:
        return False
    # Continuation after ruby: hiragana/katakana (しぶりです) — not a new dialog speaker
    if re.match(r"^[ＡABＢ]\s*[：:]", s):
        return False
    return bool(re.match(r"^[\u3040-\u30ff\u4e00-\u9fff]", s))


def stitch_broken_jp_lines(lines: list[str]) -> list[str]:
    """Join 'Ａ：あ、久' + 'しぶりです。' after furigana lines were dropped."""
    out: list[str] = []
    for line in lines:
        if out and _ends_incomplete_jp(out[-1]) and _starts_jp_continuation(line):
            out[-1] = out[-1] + line.lstrip()
        else:
            out.append(line)
    return out


def cleanup_text(raw: str) -> str:
    if not raw:
        return ""
    lines = []
    for line in raw.splitlines():
        line = _PAGE_NOISE.sub("", line)
        line = line.replace("\u3000", " ").strip()
        if not line:
            continue
        if is_likely_ruby(line):
            continue
        line = _WHITESPACE.sub(" ", line)
        lines.append(line)
    lines = stitch_broken_jp_lines(lines)
    text = "\n".join(lines)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def extract_english_blocks(text: str) -> str:
    """Keep lines that are mostly Latin (for EN can-do / instructions)."""
    out = []
    for line in text.splitlines():
        letters = sum(1 for c in line if c.isalpha())
        latin = sum(1 for c in line if ("A" <= c <= "Z") or ("a" <= c <= "z"))
        if letters and latin / max(letters, 1) > 0.6:
            out.append(line)
    return "\n".join(out)
