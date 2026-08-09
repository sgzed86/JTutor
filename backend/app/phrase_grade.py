"""Lightweight Japanese phrase grading for Whisper transcripts."""

from __future__ import annotations

import re
import unicodedata
from difflib import SequenceMatcher

DEFAULT_PASS_THRESHOLD = 58
SOFT_PASS_THRESHOLD = 48

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

# Accept any member when the rubric lists one form from the group.
_EQUIV_GROUPS: tuple[tuple[str, ...], ...] = (
    ("ありがとう", "ありがとうございます", "どうも", "どうもありがとう"),
    ("すみません", "すいません", "ごめん", "ごめんなさい"),
    ("おはよう", "おはようございます"),
    ("こんにちは",),
    ("こんばんは",),
    ("わかりません", "わからない", "よくわかりません", "よく分かりません"),
    ("もういちど", "もう一度"),
    ("じゃあまた", "じゃあ、また"),
)

_NEGATION_MARKERS = ("ません", "ない", "なく", "じゃない", "ではない")


def normalize_jp_for_grade(s: str) -> str:
    s = unicodedata.normalize("NFKC", s or "")
    for ch in " 、，,。．.！!？?「」『』・…〜～―─-－_/\t\n\r":
        s = s.replace(ch, "")
    s = s.replace(" ", "").replace("　", "")
    # Keep long vowels (ビール ≠ ビル).
    for old, new in _KANJI_VARIANTS:
        s = s.replace(old, new)
    out: list[str] = []
    for ch in s:
        code = ord(ch)
        if 0x30A1 <= code <= 0x30F6:
            out.append(chr(code - 0x60))
        else:
            out.append(ch)
    return "".join(out).strip().lower()


def expand_phrase_alternates(phrases: list[str]) -> list[str]:
    """Add polite/casual alternates for grading candidates."""
    out: list[str] = []
    seen: set[str] = set()
    for p in phrases:
        if not p:
            continue
        norm = normalize_jp_for_grade(p)
        for candidate in (p, norm):
            if candidate and candidate not in seen:
                seen.add(candidate)
                out.append(p if candidate == norm else candidate)
        pn = normalize_jp_for_grade(p)
        for group in _EQUIV_GROUPS:
            if any(normalize_jp_for_grade(g) == pn for g in group):
                for g in group:
                    gn = normalize_jp_for_grade(g)
                    if gn not in seen:
                        seen.add(gn)
                        out.append(g)
    return out or [p for p in phrases if p]


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


def _has_negation(s: str) -> bool:
    return any(m in s for m in _NEGATION_MARKERS)


def _polarity_conflict(user_n: str, expected_n: str) -> bool:
    """Affirmative vs negative mismatch (e.g. わかります vs わかりません)."""
    u_neg = _has_negation(user_n)
    e_neg = _has_negation(expected_n)
    if u_neg == e_neg:
        return False
    # Short answers where only one side has ない
    if len(user_n) < 3 or len(expected_n) < 3:
        return u_neg != e_neg
    return True


def _topic_before_suki(s: str) -> str | None:
    m = re.search(r"([\u3040-\u30ff\u4e00-\u9fff]{1,12})が好き", s)
    if m:
        return m.group(1)
    m = re.search(r"([\u3040-\u30ff\u4e00-\u9fff]{1,12})を好き", s)
    return m.group(1) if m else None


def _content_word_conflict(user_n: str, expected_n: str) -> bool:
    """Different topic in 〜が好きです-style answers."""
    u_t = _topic_before_suki(user_n)
    e_t = _topic_before_suki(expected_n)
    if u_t and e_t and u_t != e_t:
        return True
    return False


def similarity_score(user_text: str, expected: str) -> float:
    u = normalize_jp_for_grade(user_text)
    e = normalize_jp_for_grade(expected)
    if not e or not u:
        return 0.0
    if e == u:
        return 100.0
    if e in u:
        return 100.0
    if u in e and len(u) / len(e) >= 0.78:
        return 100.0

    seq = SequenceMatcher(None, u, e).ratio()
    grams = _ngram_overlap(u, e)
    blended = 0.40 * seq + 0.60 * grams
    len_ratio = min(len(u), len(e)) / max(len(u), len(e))
    if len_ratio >= 0.75 and blended >= 0.45:
        blended = min(1.0, blended + 0.12)
    score = round(min(100.0, blended * 100.0), 1)

    if _polarity_conflict(u, e):
        return min(score, 35.0)
    if _content_word_conflict(u, e):
        return min(score, 40.0)
    return score


def _soft_pass(user_text: str, expected: str, score: float) -> bool:
    u = normalize_jp_for_grade(user_text)
    e = normalize_jp_for_grade(expected)
    if _polarity_conflict(u, e) or _content_word_conflict(u, e):
        return False
    if score >= DEFAULT_PASS_THRESHOLD:
        return True
    if score < SOFT_PASS_THRESHOLD:
        return False
    if not u or not e:
        return False
    len_ratio = min(len(u), len(e)) / max(len(u), len(e))
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
    candidates = expand_phrase_alternates([p for p in expected if p and str(p).strip()])
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
        if _polarity_conflict(u_n, e_n) or _content_word_conflict(u_n, e_n):
            sc = min(sc, 35.0)
        contains_full = bool(e_n) and e_n in u_n
        ok = sc >= pass_threshold or (spoken and _soft_pass(user_text, phrase, sc)) or contains_full
        if ok and sc >= pass_threshold - 5:  # soft band still needs reasonable similarity
            if _polarity_conflict(u_n, e_n) or _content_word_conflict(u_n, e_n):
                ok = False
        if ok:
            hits.append(phrase)
        if sc > best_score:
            best_score = sc
            best_phrase = phrase

    if spoken and not hits and _soft_pass(user_text, best_phrase, best_score):
        u_n = normalize_jp_for_grade(user_text)
        e_n = normalize_jp_for_grade(best_phrase)
        if not _polarity_conflict(u_n, e_n) and not _content_word_conflict(u_n, e_n):
            hits.append(best_phrase)

    passed = bool(hits) or best_score >= pass_threshold
    if passed:
        u_n = normalize_jp_for_grade(user_text)
        e_n = normalize_jp_for_grade(best_phrase)
        if _polarity_conflict(u_n, e_n) or _content_word_conflict(u_n, e_n):
            passed = False
            hits = []

    score = round(best_score if passed else best_score, 1)
    if passed and hits:
        score = max(score, pass_threshold)
    gaps = [] if passed else [best_phrase]
    jp, en = _feedback(passed, score, best_phrase, candidates)
    return {
        "passed": passed,
        "score": score,
        "hits": hits,
        "gaps": gaps,
        "best_match": best_phrase if not passed else (hits[0] if hits else best_phrase),
        "similarity": best_score,
        "feedback_jp": jp,
        "feedback_en": en,
        "spoken": spoken,
    }


def hybrid_grade(user_text: str, must: list[str], spoken: bool) -> dict:
    return grade_phrases(user_text, must, spoken=spoken)


def quiz_grade(
    user_text: str,
    expected: list[str],
    spoken: bool,
    *,
    pass_threshold: float | None = None,
) -> dict:
    threshold = pass_threshold if pass_threshold is not None else DEFAULT_PASS_THRESHOLD
    return grade_phrases(user_text, expected, spoken=spoken, pass_threshold=threshold)
