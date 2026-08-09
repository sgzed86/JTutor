"""Irodori book exercise modes (listen → select → shadow → role-play)."""

from __future__ import annotations

# quiz_index → substep name while in `book` phase
# Design: dialog embeds a true shadowing step (full CD, no grade) before role-play,
# matching Irodori "How to Use" speaking sequence.
FLOW_BY_MODE: dict[str, list[str]] = {
    "listen_repeat": ["listen", "repeat"],
    # One CD listen, then repeat each key_phrase in order (e.g. numbers 0–10).
    "listen_repeat_all": ["listen"],  # expanded in flow_substeps()
    "listen_select": ["listen", "select"],
    # listen (understand) → shadow (fluency) → role-play (+ swap)
    "dialog": ["listen", "shadow", "partner", "learner", "swap_learner", "swap_partner"],
    # Standalone shadow-only activity (optional YAML book_mode)
    "shadow_dialog": ["shadow"],
    "pronunciation": ["listen", "pronounce"],
    "vocab_drill": ["listen", "vocab_say"],
    "kana_trace": ["listen", "trace"],
    "repeat": ["listen", "repeat"],  # legacy default
}


def book_mode(activity: dict | None) -> str:
    if not activity:
        return "listen_repeat"
    return (activity.get("book_mode") or "listen_repeat").strip()


def flow_substeps(activity: dict | None) -> list[str]:
    mode = book_mode(activity)
    if mode == "listen_repeat_all":
        phrases = [p for p in (activity or {}).get("key_phrases") or [] if p]
        n = max(len(phrases), 1)
        # listen once, then one graded repeat per phrase
        return ["listen"] + ["repeat"] * n
    return list(FLOW_BY_MODE.get(mode, FLOW_BY_MODE["listen_repeat"]))


def repeat_phrase_index(activity: dict | None, quiz_index: int) -> int | None:
    """For listen_repeat_all: which key_phrase the current repeat step targets."""
    if book_mode(activity) != "listen_repeat_all":
        return None
    if quiz_index <= 0:
        return None
    return quiz_index - 1  # quiz_index 1 → phrases[0]


def substep_at(activity: dict | None, quiz_index: int) -> str | None:
    subs = flow_substeps(activity)
    if quiz_index < 0:
        return subs[0] if subs else None
    if quiz_index >= len(subs):
        return None
    return subs[quiz_index]


def speech_substeps() -> frozenset[str]:
    """Substeps that require graded learner speech."""
    return frozenset({"repeat", "select", "learner", "swap_learner", "pronounce", "vocab_say"})


def auto_advance_substeps() -> frozenset[str]:
    """Tutor/CD-only steps — UI advances after audio (and optional TTS)."""
    return frozenset({"listen", "shadow", "partner", "swap_partner", "trace"})


def timed_audio_substeps() -> frozenset[str]:
    """Play book audio without stopping for mic/grade."""
    return frozenset({"listen", "shadow", "trace"})
