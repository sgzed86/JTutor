"""Irodori book exercise modes (listen → select → shadow → role-play).

`SUBSTEPS` is the single source of truth for what each sub-step does. The old
module-level `speech_substeps()` / `auto_advance_substeps()` sets, the per-branch
flags scattered through `lesson_flow.book_step()` and the hardcoded list in the
React client were three independent copies of this table.
"""

from __future__ import annotations

from dataclasses import dataclass

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
    "culture_read": ["listen", "reflect"],
    "repeat": ["listen", "repeat"],  # legacy default
}


@dataclass(frozen=True)
class SubStepSpec:
    """What one book sub-step does. Drives both the server flow and the client UI."""

    name: str
    expects_speech: bool
    auto_advances: bool
    plays_audio: bool
    graded: bool
    label_en: str
    hint_en: str


SUBSTEPS: dict[str, SubStepSpec] = {
    "listen": SubStepSpec(
        "listen", False, True, True, False,
        "Listen", "Play the book CD and follow along.",
    ),
    "shadow": SubStepSpec(
        "shadow", False, True, True, False,
        "Shadow", "Speak quietly along with the CD. Not graded.",
    ),
    "repeat": SubStepSpec(
        "repeat", True, False, False, True,
        "Repeat", "Say the phrase aloud.",
    ),
    "select": SubStepSpec(
        "select", True, False, False, True,
        "Choose & say", "Match the picture in your book, then say it.",
    ),
    "partner": SubStepSpec(
        "partner", False, True, False, False,
        "Partner line", "Yuki speaks the yellow line.",
    ),
    "learner": SubStepSpec(
        "learner", True, False, False, True,
        "Your line", "Say the orange line.",
    ),
    "swap_learner": SubStepSpec(
        "swap_learner", True, False, False, True,
        "Swap — you first", "Roles swapped: you speak first.",
    ),
    "swap_partner": SubStepSpec(
        "swap_partner", False, True, False, False,
        "Swap — partner", "Roles swapped: Yuki replies.",
    ),
    "pronounce": SubStepSpec(
        "pronounce", True, False, False, True,
        "Pronunciation", "Say the word clearly.",
    ),
    "vocab_say": SubStepSpec(
        "vocab_say", True, False, False, True,
        "Vocabulary", "Say each word aloud.",
    ),
    "trace": SubStepSpec(
        "trace", False, True, True, False,
        "Trace", "Listen and trace the characters in your book.",
    ),
    "reflect": SubStepSpec(
        "reflect", False, True, False, False,
        "Reflect", "Read the culture note in your book.",
    ),
}


def spec_for(substep: str | None) -> SubStepSpec | None:
    return SUBSTEPS.get(substep or "")


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
    return frozenset(name for name, spec in SUBSTEPS.items() if spec.expects_speech)


def auto_advance_substeps() -> frozenset[str]:
    """Tutor/CD-only steps — the UI continues once audio (and optional TTS) ends."""
    return frozenset(name for name, spec in SUBSTEPS.items() if spec.auto_advances)


def timed_audio_substeps() -> frozenset[str]:
    """Play book audio without stopping for mic/grade."""
    return frozenset(name for name, spec in SUBSTEPS.items() if spec.plays_audio)
