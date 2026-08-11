"""Japanese text helpers for STT prompts and grading (numbers, counters)."""

from __future__ import annotations

import re
import unicodedata

# Irodori-style readings (よん / なな / きゅう / ゼロ — not し/しち/く/れい).
_ONES = ("ゼロ", "いち", "に", "さん", "よん", "ご", "ろく", "なな", "はち", "きゅう")
_KANJI_ONES = "〇一二三四五六七八九"

_COUNTER_KANA = (
    ("歳", "さい"),
    ("才", "さい"),
    ("時", "じ"),
    ("分", "ふん"),
    ("円", "えん"),
    ("人", "にん"),
    ("月", "がつ"),
    ("日", "にち"),
    ("階", "かい"),
    ("番", "ばん"),
    ("回", "かい"),
)

_NUMBER_BANK = (
    "日本語の数字：ゼロ、いち、に、さん、よん、ご、ろく、なな、はち、きゅう、じゅう、"
    "じゅういち、にじゅう、さんじゅう、よんじゅう、ごじゅう。"
    "4歳、25歳、95歳です。"
)


def int_to_kana(n: int) -> str:
    """Cardinal reading for 0–999 (Irodori classroom style)."""
    if n < 0:
        return str(n)
    if n <= 9:
        return _ONES[n]
    if n == 10:
        return "じゅう"
    if n < 20:
        return "じゅう" + _ONES[n - 10]
    if n < 100:
        tens, ones = divmod(n, 10)
        head = _ONES[tens] + "じゅう"
        return head if ones == 0 else head + _ONES[ones]
    if n < 1000:
        hundreds, rest = divmod(n, 100)
        if hundreds == 1:
            head = "ひゃく"
        elif hundreds == 3:
            head = "さんびゃく"
        elif hundreds == 6:
            head = "ろっぴゃく"
        elif hundreds == 8:
            head = "はっぴゃく"
        else:
            head = _ONES[hundreds] + "ひゃく"
        return head if rest == 0 else head + int_to_kana(rest)
    return str(n)


def _kanji_numeral_to_int(s: str) -> int | None:
    """Parse simple kanji numerals like 二十五 / 十 / 三."""
    if not s:
        return None
    if s == "十":
        return 10
    total = 0
    if "百" in s:
        left, _, right = s.partition("百")
        h = 1 if not left else _KANJI_ONES.find(left)
        if h < 0:
            return None
        total += h * 100
        s = right
    if "十" in s:
        left, _, right = s.partition("十")
        t = 1 if not left else _KANJI_ONES.find(left)
        if t < 0:
            return None
        total += t * 10
        s = right
    if s:
        o = _KANJI_ONES.find(s)
        if o < 0:
            return None
        total += o
    return total


def digits_and_kanji_to_kana(text: str) -> str:
    """Replace Arabic / kanji number runs with kana readings (NFKC first)."""
    s = unicodedata.normalize("NFKC", text or "")

    def arab(m: re.Match[str]) -> str:
        try:
            return int_to_kana(int(m.group(0)))
        except ValueError:
            return m.group(0)

    s = re.sub(r"\d+", arab, s)

    def kanji_run(m: re.Match[str]) -> str:
        raw = m.group(0)
        n = _kanji_numeral_to_int(raw)
        return int_to_kana(n) if n is not None else raw

    s = re.sub(r"[〇一二三四五六七八九十百]+", kanji_run, s)
    # Fold counters only when they follow a numeral reading (avoid 時計→じけい).
    for kanji, kana in _COUNTER_KANA:
        s = re.sub(rf"(?<=[0-9ぁ-んァ-ン]){re.escape(kanji)}", kana, s)
    return s


def looks_numeric_or_short(hint: str) -> bool:
    h = (hint or "").strip()
    if not h:
        return False
    if re.search(r"\d|[〇一二三四五六七八九十百]|歳|才|時|分|円|ゼロ|いち|じゅう", h):
        return True
    # Ultra-short targets (いち / に / はい) need extra bias.
    compact = re.sub(r"[\s。．.、，,！!？?]+", "", h)
    return 0 < len(compact) <= 8


def build_stt_prompt(hint: str | None, *, extras: list[str] | None = None) -> str | None:
    """Bias Whisper toward the expected line and Japanese number readings."""
    parts: list[str] = []
    primary = (hint or "").strip()
    extra_bits = [e.strip() for e in (extras or []) if e and e.strip()]
    # Also bias with kana readings when the target uses digits/kanji numerals.
    for seed in [primary, *extra_bits]:
        if not seed:
            continue
        kana = digits_and_kanji_to_kana(seed)
        if kana and kana != seed and kana not in extra_bits:
            extra_bits.append(kana)
    combined = "。".join([primary, *extra_bits] if primary else extra_bits)
    if looks_numeric_or_short(combined or primary):
        parts.append(_NUMBER_BANK)
    if combined:
        parts.append(combined)
    elif primary:
        parts.append(primary)
    out = " ".join(parts).strip()
    return out[:400] if out else None


def cleanup_learner_transcript(text: str) -> str:
    """Light cleanup after Whisper (keep digits for later kana expand in grading)."""
    s = unicodedata.normalize("NFKC", text or "").strip()
    s = re.sub(r"\s+", "", s)
    # Drop common hallucinated closers on tiny clips
    for junk in ("ご視聴ありがとうございました", "字幕", "字幕作成者", "Thank you", "Thanks for watching"):
        if junk in s and len(s) < len(junk) + 8:
            return ""
    return s
