"""Free-response helpers for intro_chat (no grading)."""

from __future__ import annotations


def intro_questions(lesson: dict) -> list[dict]:
    """
    Normalize lesson.intro_questions into [{jp, en}, ...].
    Accepts strings or dicts; empty → [].
    """
    raw = lesson.get("intro_questions") or []
    out: list[dict] = []
    for item in raw:
        if isinstance(item, str) and item.strip():
            out.append({"jp": item.strip(), "en": item.strip()})
        elif isinstance(item, dict):
            jp = (item.get("jp") or item.get("question_jp") or "").strip()
            en = (item.get("en") or item.get("question_en") or jp).strip()
            if jp or en:
                out.append({"jp": jp or en, "en": en or jp})
    return out[:4]


def intro_turn_count(lesson: dict) -> int:
    """One free answer per intro question (N turns)."""
    return max(len(intro_questions(lesson)), 0)


def acknowledge_intro(answer: str) -> tuple[str, str]:
    """Short acknowledgment — no scoring."""
    a = (answer or "").strip()
    if len(a) < 2:
        return "もうすこし いってみてください。", "Say a little more if you can — or tap Skip."
    return "ありがとうございます。", "Thanks for sharing. Let's continue."


def intro_step(lesson: dict, question_index: int) -> tuple[str, str, dict]:
    qs = intro_questions(lesson)
    if not qs:
        step = {
            "phase": "intro_chat",
            "book_mode": "intro_chat",
            "book_substep": "done",
            "expect_speech": False,
            "auto_advance_after_audio": True,
            "play_audio": [],
        }
        return "では、れんしゅうを はじめます。", "Let's start the book exercises.", step
    q = qs[min(question_index, len(qs) - 1)]
    jp = q["jp"]
    en = q["en"]
    step = {
        "phase": "intro_chat",
        "book_mode": "intro_chat",
        "book_substep": "free_answer",
        "expect_speech": True,
        "auto_advance_after_audio": False,
        "play_audio": [],
        "intro_question_index": question_index,
        "intro_question_total": len(qs),
        "instruction_en": "Warm-up — answer freely (any language is OK).",
        "say_target_jp": None,
    }
    return jp, en, step
