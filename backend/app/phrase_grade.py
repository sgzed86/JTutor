"""Lightweight Japanese phrase grading for Whisper transcripts."""

from __future__ import annotations

import re
import unicodedata
from difflib import SequenceMatcher

# Spoken / STT grading is intentionally soft — exact kanji vs kana should not block.
DEFAULT_PASS_THRESHOLD = 58
# Soft pass when close and length is in the same ballpark (Whisper near-misses).
SOFT_PASS_THRESHOLD = 48

# Common learner / STT normalizations (applied before compare). Longer keys first.
_KANJI_VARIANTS = (
    ("分かりません", "わかりません"),
    ("分かります", "わかります"),
    ("分かり", "わかり"),
    ("分から", "わから"),
    ("分か", "わか"),
    ("もう一度", "もういちど"),
    ("もう少し", "もうすこし"),
    ("少し", "すこし"),
    ("下さい", "ください"),
    ("お願い", "おねがい"),
    ("言って", "いって"),
    ("言う", "いう"),
    ("有難う", "ありがとう"),
    ("有り難う", "ありがとう"),
    ("ありがとう御座います", "ありがとうございます"),
    ("済みません", "すみません"),
    ("済ません", "すいません"),
    ("日本語", "にほんご"),
    ("英語", "えいご"),
    ("中国語", "ちゅうごくご"),
    ("インドネシア語", "いんどねしあご"),
    ("出来ます", "できます"),
    ("出来る", "できる"),
    ("出来", "でき"),
)


def normalize_jp_for_grade(s: str) -> str:
    s = unicodedata.normalize("NFKC", s or "")
    # Drop punctuation / spaces / common filler length marks used inconsistently by STT
    for ch in " 、，,。．.！!？?「」『』・…〜～―─-－_/\t\n\r":
        s = s.replace(ch, "")
    s = s.replace(" ", "")
    s = s.replace("　", "")
    # Collapse prolonged sound marks (ごー ≈ ご for short answers)
    s = re.sub(r"[ー∼]+", "", s)
    for old, new in _KANJI_VARIANTS:
        s = s.replace(old, new)
    # Katakana → hiragana for compare (ゼロ/ぜろ, etc.)
    out: list[str] = []
    for ch in s:
        code = ord(ch)
        if 0x30A1 <= code <= 0x30F6:
            out.append(chr(code - 0x60))
        else:
            out.append(ch)
    return "".join(out).strip().lower()


def _char_ngrams(s: str, n: int = 2) -> set[str]:
    if not s:
        return set()
    if len(s) < n:
        return {s}
    return {s[i : i + n] for i in range(len(s) - n + 1)}


def _ngram_overlap(a: str, b: str) -> float:
    ta, tb = _char_ngrams(a), _char_ngrams(b)
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / max(len(ta), len(tb))


def similarity_score(user_text: str, expected: str) -> float:
    """0–100 similarity between utterance and one expected phrase."""
    u = normalize_jp_for_grade(user_text)
    e = normalize_jp_for_grade(expected)
    if not e or not u:
        return 0.0
    if e == u:
        return 100.0
    # User said the full target plus filler → pass
    if e in u:
        return 100.0
    # User is a near-complete form of the target (not a short fragment like 「もう」)
    if u in e and len(u) / len(e) >= 0.78:
        return 100.0

    seq = SequenceMatcher(None, u, e).ratio()
    grams = _ngram_overlap(u, e)
    # Prefer n-gram overlap for JP (kanji/kana mix used to tank pure seq ratio)
    blended = 0.40 * seq + 0.60 * grams

    # Length-similar near miss bonus (e.g. one mora off)
    len_ratio = min(len(u), len(e)) / max(len(u), len(e))
    if len_ratio >= 0.75 and blended >= 0.45:
        blended = min(1.0, blended + 0.12)

    return round(min(100.0, blended * 100.0), 1)


def _soft_pass(user_text: str, expected: str, score: float) -> bool:
    if score >= DEFAULT_PASS_THRESHOLD:
        return True
    if score < SOFT_PASS_THRESHOLD:
        return False
    u = normalize_jp_for_grade(user_text)
    e = normalize_jp_for_grade(expected)
    if not u or not e:
        return False
    len_ratio = min(len(u), len(e)) / max(len(u), len(e))
    # Soft: close score + similar length, or expected mostly covered by user chars
    if len_ratio >= 0.7:
        return True
    shared = sum(1 for ch in e if ch in u)
    return shared / len(e) >= 0.7


def _feedback(passed: bool, score: float, best: str | None, expected: list[str]) -> tuple[str, str]:
    if passed:
        return ("よくできました。", "Nice — that matches the target phrase.")
    target = best or (expected[0] if expected else "")
    if score >= 45:
        jp = f"ちかいです。もういちど：{target}" if target else "ちかいです。もういちど。"
        en = f"Close ({score:.0f}%). Try again: {target}" if target else f"Close ({score:.0f}%). Try again."
    else:
        jp = f"もういちど いってください。{target}" if target else "もういちど いってください。"
        en = f"Say it again — target: {target}" if target else "Say it again."
    return jp, en


def grade_phrases(
    user_text: str,
    expected: list[str],
    *,
    spoken: bool = True,
    pass_threshold: float = DEFAULT_PASS_THRESHOLD,
) -> dict:
    """
    Compare transcript to one or more acceptable phrases.
    Returns pass/fail, score, hits, gaps, and UI feedback strings.
    """
    candidates = [p for p in expected if p and str(p).strip()]
    if not candidates:
        has_jp = bool(re.search(r"[\u3040-\u30ff\u4e00-\u9fff]", user_text or ""))
        passed = has_jp and len((user_text or "").strip()) >= 2
        score = 80.0 if passed else 30.0
        jp, en = _feedback(passed, score, None, [])
        return {
            "passed": passed,
            "score": score,
            "hits": [],
            "gaps": [],
            "best_match": None,
            "similarity": score,
            "feedback_jp": jp,
            "feedback_en": en,
            "spoken": spoken,
        }

    best_phrase = candidates[0]
    best_score = 0.0
    hits: list[str] = []
    for phrase in candidates:
        sc = similarity_score(user_text, phrase)
        u_n = normalize_jp_for_grade(user_text)
        e_n = normalize_jp_for_grade(phrase)
        contains_full = bool(e_n) and e_n in u_n
        ok = sc >= pass_threshold or (spoken and _soft_pass(user_text, phrase, sc)) or contains_full
        if ok:
            hits.append(phrase)
        if sc > best_score:
            best_score = sc
            best_phrase = phrase

    # Soft pass on best candidate even if threshold loop missed (spoken only)
    if spoken and not hits and _soft_pass(user_text, best_phrase, best_score):
        hits.append(best_phrase)

    passed = bool(hits) or best_score >= pass_threshold
    score = 100.0 if passed and hits else best_score
    gaps = [] if passed else [best_phrase]
    jp, en = _feedback(passed, score, best_phrase, candidates)
    return {
        "passed": passed,
        "score": round(score, 1),
        "hits": hits,
        "gaps": gaps,
        "best_match": best_phrase if not passed else (hits[0] if hits else best_phrase),
        "similarity": best_score,
        "feedback_jp": jp,
        "feedback_en": en,
        "spoken": spoken,
    }


def hybrid_grade(user_text: str, must: list[str], spoken: bool) -> dict:
    """Drop-in replacement for orchestrator grading."""
    return grade_phrases(user_text, must, spoken=spoken)


def quiz_grade(user_text: str, expected: list[str], spoken: bool) -> dict:
    g = grade_phrases(user_text, expected, spoken=spoken)
    if expected and not g["passed"]:
        g["score"] = max(g["score"], 40.0)
    return g
