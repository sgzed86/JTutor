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
    # One CD listen, then type each curated blank line (Irodori 書きましょう).
    "listen_fill": ["listen"],  # expanded in flow_substeps()
    # True comprehension: listen, then tap choices (not “say the phrase”).
    "listen_choose": ["listen", "choose"],
    "listen_select": ["listen", "select"],  # legacy speak-after-picture
    # Typed notes after listening (ungraded / soft keyword check).
    "note_take": ["listen", "note"],
    # Read a passage / menu / notice, then answer.
    "reading": ["read", "read_check"],
    # listen (understand) → shadow (fluency) → role-play (+ swap)
    "dialog": ["listen", "shadow", "partner", "learner", "swap_learner", "swap_partner"],
    # Standalone shadow-only activity (optional YAML book_mode)
    "shadow_dialog": ["shadow"],
    "pronunciation": ["listen"],  # expanded per phrase
    "vocab_drill": ["listen"],  # expanded per phrase
    "kana_trace": ["listen", "trace"],
    "culture_read": ["reflect"],
    "kanji_words": ["kanji_study"],  # expanded in flow_substeps()
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
    expects_text: bool = False


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
    "fill": SubStepSpec(
        "fill", False, False, False, True,
        "Fill in", "Type the missing words you heard.",
        expects_text=True,
    ),
    "choose": SubStepSpec(
        "choose", False, False, False, True,
        "Choose", "Tap what you heard.",
        expects_text=True,
    ),
    "note": SubStepSpec(
        "note", False, False, False, True,
        "Notes", "Type brief notes about what you heard.",
        expects_text=True,
    ),
    "read": SubStepSpec(
        "read", False, False, False, False,
        "Read", "Read the passage in your book / on screen.",
    ),
    "read_check": SubStepSpec(
        "read_check", False, False, False, True,
        "Check", "Answer about what you read.",
        expects_text=True,
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
        "Swap — you first", "Roles swapped: you speak the yellow line first.",
    ),
    "swap_partner": SubStepSpec(
        "swap_partner", False, True, False, False,
        "Swap — partner", "Roles swapped: Yuki speaks the orange line.",
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
        "reflect", False, False, False, False,
        "Reflect", "Read the culture note in your book.",
    ),
    "kanji_study": SubStepSpec(
        "kanji_study", False, False, False, False,
        "Kanji words", "Check each kanji and its reading.",
    ),
    "kanji_read": SubStepSpec(
        "kanji_read", False, False, False, False,
        "Read", "Read the example lines with the new kanji.",
    ),
    "kanji_type": SubStepSpec(
        "kanji_type", False, False, False, True,
        "Type", "Type the kanji word (IME is fine).",
        expects_text=True,
    ),
}


def spec_for(substep: str | None) -> SubStepSpec | None:
    return SUBSTEPS.get(substep or "")


def book_mode(activity: dict | None) -> str:
    if not activity:
        return "listen_repeat"
    return (activity.get("book_mode") or "listen_repeat").strip()


def activity_key_phrases(activity: dict | None) -> list[str]:
    return [str(p).strip() for p in (activity or {}).get("key_phrases") or [] if str(p).strip()]


def flow_substeps(activity: dict | None) -> list[str]:
    mode = book_mode(activity)
    if mode == "listen_repeat_all":
        phrases = activity_key_phrases(activity)
        n = max(len(phrases), 1)
        return ["listen"] + ["repeat"] * n
    if mode == "listen_fill":
        blanks = [
            b
            for b in (activity or {}).get("blanks") or []
            if (b.get("prompt_jp") if isinstance(b, dict) else getattr(b, "prompt_jp", None))
        ]
        n = max(len(blanks), 1)
        return ["listen"] + ["fill"] * n
    if mode in ("vocab_drill", "pronunciation"):
        phrases = activity_key_phrases(activity)
        n = max(len(phrases), 1)
        step = "vocab_say" if mode == "vocab_drill" else "pronounce"
        return ["listen"] + [step] * n
    if mode == "culture_read":
        # Student reads Life & culture on their own — no listen/CD auto chain.
        return ["reflect"]
    if mode == "reading":
        if (activity or {}).get("choices") or (activity or {}).get("blanks"):
            return ["read", "read_check"]
        return ["read"]
    if mode == "kanji_words":
        items = [
            it
            for it in (activity or {}).get("kanji_items") or []
            if isinstance(it, dict) and (it.get("kanji") or "").strip()
        ]
        n = max(len(items), 1)
        # Study all cards → read example lines → type each word
        return ["kanji_study", "kanji_read"] + ["kanji_type"] * n
    return list(FLOW_BY_MODE.get(mode, FLOW_BY_MODE["listen_repeat"]))


def phrase_drill_index(activity: dict | None, quiz_index: int, *, modes: set[str]) -> int | None:
    if book_mode(activity) not in modes:
        return None
    if quiz_index <= 0:
        return None
    return quiz_index - 1


def repeat_phrase_index(activity: dict | None, quiz_index: int) -> int | None:
    """For listen_repeat_all: which key_phrase the current repeat step targets."""
    return phrase_drill_index(activity, quiz_index, modes={"listen_repeat_all"})


def fill_blank_index(activity: dict | None, quiz_index: int) -> int | None:
    """For listen_fill: which blanks[] item the current fill step targets."""
    return phrase_drill_index(activity, quiz_index, modes={"listen_fill"})


def vocab_phrase_index(activity: dict | None, quiz_index: int) -> int | None:
    return phrase_drill_index(activity, quiz_index, modes={"vocab_drill"})


def pronounce_phrase_index(activity: dict | None, quiz_index: int) -> int | None:
    return phrase_drill_index(activity, quiz_index, modes={"pronunciation"})


def kanji_type_index(activity: dict | None, quiz_index: int) -> int | None:
    """Index into kanji_items for the current kanji_type step (after study+read)."""
    if book_mode(activity) != "kanji_words":
        return None
    # flow: [study, read] + type*n  → first type is quiz_index 2
    if quiz_index < 2:
        return None
    return quiz_index - 2


def graded_substeps() -> frozenset[str]:
    """Substeps that accept a graded learner answer (speech or typed)."""
    return frozenset(name for name, spec in SUBSTEPS.items() if spec.graded)


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
