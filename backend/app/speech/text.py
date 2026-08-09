"""The single implementation of tutor-text normalization for speech.

This used to exist twice: `apps/desktop/src/speech.ts::speakableText` on the
client and `voicevox_client.prepare_for_voicevox` on the server, with different
regexes, both applied in sequence. The server now owns it; the client sends raw
text.
"""

from __future__ import annotations

import re

_JP_RANGE = r"\u3040-\u30ff\u4e00-\u9fff"
_HAS_JP = re.compile(f"[{_JP_RANGE}]")
_CODE_FENCE = re.compile(r"```[\s\S]*?```")
_MARKDOWN = re.compile(r"[*_`#]+")
_ASCII_PAREN = re.compile(r"\([A-Za-z][^)]{0,80}\)")
_LATIN_RUN = re.compile(r"[A-Za-z]{3,}")
_WS = re.compile(r"\s+")
_SENTENCE_END = re.compile(r"(?<=[。！？!?…])\s*")

MAX_SYNTH_CHARS = 300


def speakable_text(raw: str, *, drop_latin_when_jp: bool = True) -> str:
    """Strip markup and English glosses so the engine speaks the tutor line."""
    text = (raw or "").strip()
    text = _CODE_FENCE.sub(" ", text)
    text = _MARKDOWN.sub(" ", text)
    text = _ASCII_PAREN.sub(" ", text)
    text = _WS.sub(" ", text).strip()
    if drop_latin_when_jp and _HAS_JP.search(text):
        # VOICEVOX spells out long Latin runs letter by letter; drop them when
        # there is Japanese to say instead.
        text = _WS.sub(" ", _LATIN_RUN.sub(" ", text)).strip()
    return text


def has_japanese(text: str) -> bool:
    return bool(_HAS_JP.search(text or ""))


def split_utterances(text: str, max_len: int = 80) -> list[str]:
    """Break a line into engine-sized chunks on sentence boundaries."""
    parts = [p.strip() for p in _SENTENCE_END.split(text or "") if p and p.strip()]
    out: list[str] = []
    for part in parts or ([text] if text else []):
        if len(part) <= max_len:
            out.append(part)
            continue
        for i in range(0, len(part), max_len):
            out.append(part[i : i + max_len])
    return [p for p in out if p]


def prepare_for_voicevox(text: str) -> str:
    """Normalized, length-capped text handed to the synthesis engine."""
    return speakable_text(text)[:MAX_SYNTH_CHARS]
