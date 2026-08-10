"""Derive tutor key_phrases from Whisper transcripts (L03+)."""

from __future__ import annotations

import re
import unicodedata

_JP_RE = re.compile(r"[\u3040-\u30ff\u4e00-\u9fff]")


def _norm(s: str) -> str:
    s = unicodedata.normalize("NFKC", s or "")
    s = re.sub(r"\s+", "", s)
    return s.strip()


def _jp_len(s: str) -> int:
    return len(_JP_RE.findall(s))


# Common Whisper glitches on Irodori Starter classroom audio.
_WHISPER_FIXES: tuple[tuple[str, str], ...] = (
    (r"^(\d{1,2})(?=[\u3040-\u30ff\u4e00-\u9fff])", ""),  # leading track digits
    ("ご視聴", "ご出身"),
    ("ご視聖", "ご出身"),
    ("ご主信", "ご出身"),
    ("体から", "タイから"),
    ("やんまわ", "ミャンマー"),
    ("パクソン人", "韓国人"),
    ("増えです", "ハノイです"),
    ("はのい", "ハノイ"),
    ("貢猛地", "カンボジア"),
    ("看望地", "カンボジア"),
    ("始めまして", "はじめまして"),
    ("初めまして", "はじめまして"),
    # L04 family / age / home
    ("ピリピン", "フィリピン"),
    ("喜しく", "よろしく"),
    ("赤場", "赤羽"),
    ("参細", "3歳"),
    ("死ぬやま", "下山"),
    ("二乗へ", "井上"),
    ("イモート", "いもうと"),
    ("お父と", "おとうと"),
    ("ペットの上", "ペットのジョン"),
    ("雨の子供", "あねの子ども"),
)


def cleanup_transcript(text: str) -> str:
    """Normalize Whisper text before phrase picking."""
    s = _norm(text)
    if not s:
        return ""
    for pat, repl in _WHISPER_FIXES:
        s = re.sub(pat, repl, s)
    # Break run-on intros after clause endings / before set greetings.
    s = re.sub(r"(です)(?=[\u3040-\u30ff\u4e00-\u9fff])", r"\1。", s)
    s = re.sub(r"(ました)(?=[\u3040-\u30ff\u4e00-\u9fff])", r"\1。", s)
    s = re.sub(r"(?<![。])(はじめまして)", r"。\1", s)
    s = re.sub(r"(?<![。])(どうぞ?よろしくお願いします)", r"。\1", s)
    s = re.sub(r"。+", "。", s).strip("。")
    return s


def split_sentences(text: str) -> list[str]:
    text = cleanup_transcript(text)
    if not text:
        return []
    parts = re.split(r"(?<=[。！？!?])", text)
    out: list[str] = []
    for p in parts:
        p = p.strip("。！？!?、，,. ")
        # Drop leftover bare track numbers / tiny fragments
        if re.fullmatch(r"\d{1,2}", p):
            continue
        if _jp_len(p) >= 2:
            out.append(p)
    if not out and _jp_len(text) >= 2:
        out = [text]
    # Prefer speakable chunks: split still-too-long intros on です／ました
    refined: list[str] = []
    for p in out:
        if _jp_len(p) <= 28:
            refined.append(p)
            continue
        chunks = re.split(r"(?<=です)|(?<=ました)|(?<=ます)", p)
        buf = ""
        for ch in chunks:
            ch = ch.strip("。 ")
            if not ch:
                continue
            buf += ch
            if _jp_len(buf) >= 6 and re.search(r"(です|ました|ます|ください)$", buf):
                refined.append(buf)
                buf = ""
        if buf and _jp_len(buf) >= 2:
            refined.append(buf)
    return refined or out


def _score_phrase(s: str, kind: str) -> float:
    score = min(_jp_len(s), 40) / 40.0
    if kind == "listening":
        if re.search(r"(ますか|ですか|でしょうか|ください|ませんか)", s):
            score += 0.35
        if re.search(r"(わかり|できます|好き|住んで|どこ|いくら|行き)", s):
            score += 0.15
    if kind in ("speaking", "conversation"):
        if re.search(r"(です|ました|ください|よろしく|はじめまして)", s):
            score += 0.2
    if _jp_len(s) < 4:
        score -= 0.25
    if _jp_len(s) > 55:
        score -= 0.15
    return score


def pick_phrases(transcript: str, kind: str, max_phrases: int = 4) -> list[str]:
    sents = split_sentences(transcript)
    if not sents:
        t = _norm(transcript)
        return [t] if _jp_len(t) >= 2 else []
    ranked = sorted(sents, key=lambda s: _score_phrase(s, kind), reverse=True)
    out: list[str] = []
    seen: set[str] = set()
    for s in ranked:
        key = _norm(s)
        if key in seen:
            continue
        seen.add(key)
        out.append(s)
        if len(out) >= max_phrases:
            break
    # Stable fallback: also include first/last sentence for dialog-style clips
    if sents[0] not in out and len(out) < max_phrases:
        out.append(sents[0])
    if len(sents) > 1 and sents[-1] not in out and len(out) < max_phrases:
        out.append(sents[-1])
    return out[:max_phrases]


def infer_dialog(transcript: str) -> tuple[str, str] | None:
    sents = split_sentences(transcript)
    if len(sents) < 2:
        return None
    partner = None
    for s in sents:
        if re.search(r"(ますか|ですか|ませんか|でしょうか)$", _norm(s)) or "？" in s or "?" in s:
            partner = s
            break
    if not partner:
        partner = sents[0]
    learner = sents[-1]
    if _norm(learner) == _norm(partner) and len(sents) >= 2:
        learner = sents[1]
    if _jp_len(partner) < 2 or _jp_len(learner) < 2:
        return None
    return partner, learner
