"""Structured Irodori lesson flow — scripted A1 steps, no free-form teaching chat."""

from __future__ import annotations

import json

from backend.app.book_modes import (
    book_mode,
    flow_substeps,
    repeat_phrase_index,
    spec_for,
    substep_at,
)
from backend.app.books import content_dir_for_lesson
from backend.app.curriculum_loader import load_lesson

_transcript_cache: dict[str, dict[str, str]] = {}


def audio_transcripts(lesson_id: str) -> dict[str, str]:
    """Whisper transcripts for the book MP3s, keyed by relative path.

    Optional: the file is excluded from some packaged builds, in which case the
    Script tab simply has nothing extra to show.
    """
    key = str(content_dir_for_lesson(lesson_id))
    cached = _transcript_cache.get(key)
    if cached is not None:
        return cached
    path = content_dir_for_lesson(lesson_id) / "audio_transcripts.json"
    data: dict[str, str] = {}
    if path.is_file():
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(raw, dict):
                data = {str(k): str(v) for k, v in raw.items()}
        except (OSError, json.JSONDecodeError):
            data = {}
    _transcript_cache[key] = data
    return data


def audio_entries(lesson_id: str, paths: list[str]) -> list[dict]:
    """Audio descriptors with transcripts, so the client can show a script."""
    transcripts = audio_transcripts(lesson_id)
    return [{"path": p, "transcript": transcripts.get(p)} for p in paths if p]


def lesson_segments(lesson: dict) -> list[dict]:
    """Consecutive activities sharing a can_do_id form one presentational segment.

    Purely for display — the orchestrator does not use segments to sequence
    anything.
    """
    segments: list[dict] = []
    for activity in book_tracks(lesson):
        cid = activity.get("can_do_id")
        if segments and segments[-1]["can_do_id"] == cid:
            segments[-1]["activity_ids"].append(activity.get("id"))
            continue
        title = None
        for cd in lesson.get("can_dos") or []:
            if cd.get("id") == cid:
                title = cd.get("statement_en")
                break
        segments.append(
            {
                "index": len(segments),
                "can_do_id": cid,
                "title_en": title,
                "activity_ids": [activity.get("id")],
            }
        )
    for seg in segments:
        seg["total"] = len(segments)
    return segments


def segment_for_activity(lesson: dict, activity_id: str | None) -> dict | None:
    if not activity_id:
        return None
    for seg in lesson_segments(lesson):
        if activity_id in seg["activity_ids"]:
            return {
                "index": seg["index"],
                "total": seg["total"],
                "can_do_id": seg["can_do_id"],
                "title_en": seg["title_en"],
            }
    return None


def _grammar_for_lesson(lesson_id: str) -> list[dict]:
    lesson = load_lesson(lesson_id)
    points = lesson.get("grammar") or []
    if points:
        return points
    grammar_json = content_dir_for_lesson(lesson_id) / "grammar_extract.json"
    if not grammar_json.is_file():
        return []
    data = json.loads(grammar_json.read_text(encoding="utf-8"))
    g = data.get("lessons", {}).get(lesson_id, {})
    return [{"point": p["point"], "worksheet_pages": [p.get("page")]} for p in g.get("points", [])]


def book_tracks(lesson: dict) -> list[dict]:
    """One Irodori activity per step (book order)."""
    skip = {"script"}
    if lesson.get("lesson_id") != "L00":
        skip.add("classroom")
    acts = [
        a
        for a in (lesson.get("activities") or [])
        if a.get("kind") not in skip and not a.get("book_skip")
    ]
    acts.sort(key=lambda x: int(x.get("book_activity") or 0))
    return acts


def track_by_id(lesson: dict, activity_id: str | None) -> dict | None:
    if not activity_id:
        return None
    for t in book_tracks(lesson):
        if t.get("id") == activity_id:
            return t
    for a in lesson.get("activities") or []:
        if a.get("id") == activity_id:
            return a
    return None


def track_index(lesson: dict, activity_id: str | None) -> int:
    tracks = book_tracks(lesson)
    if not activity_id:
        return 0
    for i, t in enumerate(tracks):
        if t.get("id") == activity_id:
            return i
    return 0


def _phrases(activity: dict | None) -> list[str]:
    if not activity:
        return []
    return [p for p in (activity.get("key_phrases") or []) if p]


def _lesson_num(lesson_id: str) -> str:
    from backend.app.books import parse_lesson_num

    n = parse_lesson_num(lesson_id)
    return str(n) if n is not None else lesson_id


def intro_script(lesson: dict) -> tuple[str, str]:
    """Returns (spoken_jp, hint_en)."""
    n = _lesson_num(lesson["lesson_id"])
    title = lesson.get("title_jp") or lesson.get("title_en") or ""
    pages = lesson.get("pdf_pages") or []
    page_hint = f" Open the book around page {pages[0]}." if pages else ""
    jp = (
        f"こんにちは。れっすん{n}です。"
        f"「{title}」。"
        f"いっしょに、ほんの れんしゅうを します。"
    )
    en = (
        f"Lesson {n}: {lesson.get('title_en')}.{page_hint} "
        f"We will do the book exercises in order, then grammar (if any), then Can-do checks."
    )
    return jp, en


def _dialog_lines(activity: dict) -> list[dict]:
    return list(activity.get("dialog_script") or [])


def _dialog_line(activity: dict, substep: str) -> dict | None:
    lines = _dialog_lines(activity)
    if not lines:
        return None
    swap = substep.startswith("swap_")
    want = "partner" if "partner" in substep else "learner"
    pool = (
        lines
        if not swap
        else [
            {**ln, "speaker": "learner" if ln.get("speaker") == "partner" else "partner"}
            for ln in lines
        ]
    )
    for ln in pool:
        if ln.get("speaker") == want:
            return ln
    return lines[0] if lines else None


def _step_base(activity: dict, substep: str, quiz_index: int, lesson: dict | None = None) -> dict:
    subs = flow_substeps(activity)
    spec = spec_for(substep)
    step = {
        "phase": "book",
        "book_mode": book_mode(activity),
        "book_substep": substep,
        "activity_id": activity.get("id"),
        "book_activity": activity.get("book_activity"),
        "kind": activity.get("kind"),
        "book_flow_index": quiz_index,
        "section_title_en": activity.get("book_section_en"),
        # Self-describing fields so the client never has to re-derive the flow.
        "substeps": subs,
        "substep_index": quiz_index if 0 <= quiz_index < len(subs) else None,
        "substep_total": len(subs),
        "expects_speech": bool(spec and spec.expects_speech),
        "auto_advance": bool(spec and spec.auto_advances),
        "graded": bool(spec and spec.graded),
        "substep_label_en": spec.label_en if spec else None,
    }
    if lesson:
        step["activity_index"] = track_index(lesson, activity.get("id"))
        step["activity_total"] = len(book_tracks(lesson))
        step["segment"] = segment_for_activity(lesson, activity.get("id"))
    return step


def book_step(activity: dict, lesson: dict, quiz_index: int) -> tuple[str, str, dict]:
    """One book sub-step, with audio/script metadata attached for the client."""
    jp, en, step = _book_step_impl(activity, lesson, quiz_index)
    lesson_id = str(lesson.get("lesson_id") or "") if lesson else ""
    if lesson_id:
        step["audio"] = audio_entries(lesson_id, list(step.get("play_audio") or []))
    if activity.get("dialog_script") and "dialog_script" not in step:
        step["dialog_script"] = activity.get("dialog_script")
    return jp, en, step


def _book_step_impl(activity: dict, lesson: dict, quiz_index: int) -> tuple[str, str, dict]:
    """One book sub-step (listen / select / role-play line)."""
    sub = substep_at(activity, quiz_index) or "repeat"
    phrases = _phrases(activity)
    audio = list(activity.get("dialog_listen_audio") or activity.get("audio") or [])

    if sub == "listen":
        mode = book_mode(activity)
        if mode == "culture_read":
            jp = "文化の メモを よみましょう。CDを きいてください。"
            en = "Life and culture — listen, then read the notes in your book."
            step = _step_base(activity, sub, quiz_index)
            step.update(
                {
                    "play_audio": audio[:2],
                    "expect_speech": False,
                    "auto_advance_after_audio": True,
                    "instruction_en": "Culture notes (listen)",
                    "book_mode": "culture_read",
                    "culture_notes_en": (lesson.get("english_notes") or "")[:600],
                }
            )
            return jp, en, step
        if mode == "kana_trace":
            jp = "ききましょう。CDを きいて、もじを なぞって れんしゅう してください。"
            en = "Listen to the CD and trace the characters in your book. No speaking grade."
            step = _step_base(activity, sub, quiz_index)
            step.update(
                {
                    "play_audio": audio[:2],
                    "expect_speech": False,
                    "auto_advance_after_audio": True,
                    "instruction_en": "Listen and trace kana in the book",
                    "book_mode": "kana_trace",
                }
            )
            return jp, en, step
        if mode == "vocab_drill":
            jp = "ことばを ききましょう。CDを きいてください。"
            en = "Vocabulary — listen to the CD, then say each word in Japanese."
            up_next = f"Next say: {phrases[0]}" if phrases else None
        elif mode == "pronunciation":
            jp = "はつおんに ちゅういして ききましょう。CDを きいてください。"
            en = "Pronunciation — listen for rhythm and long vowels, then repeat carefully."
            up_next = f"Next pronounce: {phrases[0]}" if phrases else None
        elif mode == "listen_repeat_all":
            jp = "聞いて、言いましょう。CDを きいてください。"
            n = len(phrases)
            en = (
                f"Listen to the CD (0–10), then repeat each number ({n} in all)."
                if n
                else "Listen to the CD, then repeat each phrase."
            )
            up_next = f"Next you will say each number, starting with: {phrases[0]}" if phrases else None
        elif mode == "listen_repeat":
            jp = "聞いて、言いましょう。CDを きいてください。"
            en = "Listen and repeat — play the CD, then say the phrase."
            up_next = f"Next you will say: {phrases[0]}" if phrases else None
        elif mode == "listen_select":
            jp = "えを 見て、ききましょう。CDを きいてください。"
            en = activity.get("picture_hint_en") or "Look at the picture in the book, then listen."
            up_next = None
        else:
            jp = "会話を ききましょう。CDを きいてください。"
            en = activity.get("book_scene_en") or "Listen to the dialog on the CD."
            up_next = None
        step = _step_base(activity, sub, quiz_index, lesson)
        step.update(
            {
                "play_audio": audio[:2],
                "expect_speech": False,
                "auto_advance_after_audio": True,
                "instruction_en": "Listen to the book CD first",
                "picture_hint_en": activity.get("picture_hint_en"),
                "say_target_jp": phrases[0] if phrases else None,
                "say_alternates_jp": phrases[1:4] if mode != "listen_repeat_all" else [],
                "up_next_en": up_next,
                "phrase_total": len(phrases) if mode == "listen_repeat_all" else None,
            }
        )
        return jp, en, step

    if sub == "reflect":
        notes = (lesson.get("english_notes") or activity.get("culture_notes_en") or "").strip()
        jp = "文化について かんがえましょう。"
        en = notes[:400] or "Read the culture notes in your book. No grade — tap Skip when ready."
        step = _step_base(activity, sub, quiz_index)
        step.update(
            {
                "play_audio": [],
                "expect_speech": False,
                "auto_advance_after_audio": True,
                "instruction_en": en,
                "book_mode": "culture_read",
                "culture_card": True,
            }
        )
        return jp, en, step

    if sub == "trace":
        jp = "もじを なぞって れんしゅう しましょう。こたえは ありません。"
        en = "Trace the characters in your book. This step is not graded — tap Skip when ready."
        step = _step_base(activity, sub, quiz_index)
        step.update(
            {
                "play_audio": [],
                "expect_speech": False,
                "auto_advance_after_audio": True,
                "instruction_en": "Trace kana in the book (ungraded)",
                "book_mode": "kana_trace",
                "shadow_card": True,
            }
        )
        return jp, en, step

    if sub == "pronounce":
        target = phrases[0] if phrases else ""
        jp = f"はつおんを たしかに いってください。{target}" if target else "はつおんを たしかに いってください。"
        en = f"Pronunciation — say clearly (watch long vowels): {target}" if target else "Say the phrase clearly."
        step = _step_base(activity, sub, quiz_index)
        step.update(
            {
                "play_audio": audio[:1],
                "expect_speech": True,
                "auto_advance_after_audio": False,
                "instruction_en": "Focus on mora and long vowels",
                "say_target_jp": target or None,
                "say_alternates_jp": phrases[1:3],
                "book_mode": "pronunciation",
            }
        )
        return jp, en, step

    if sub == "vocab_say":
        target = phrases[0] if phrases else ""
        gloss = (activity.get("vocab_gloss_en") or activity.get("gloss_en") or "").strip()
        jp = f"ことばを いってください。{target}" if target else "ことばを いってください。"
        en = f"Say the vocabulary word in Japanese{f' ({gloss})' if gloss else ''}: {target}"
        step = _step_base(activity, sub, quiz_index)
        step.update(
            {
                "play_audio": [],
                "expect_speech": True,
                "auto_advance_after_audio": False,
                "instruction_en": en,
                "say_target_jp": target or None,
                "gloss_en": gloss or None,
                "book_mode": "vocab_drill",
            }
        )
        return jp, en, step

    if sub == "shadow":
        # Full dialog CD for shadowing — no mic, no grade (Irodori speaking step 2).
        jp = "シャドーイングしましょう。CDに 合わせて、小声で いってください。"
        en = (
            "Shadow the dialog — speak quietly along with the CD. "
            "No grading; just follow the rhythm."
        )
        step = _step_base(activity, sub, quiz_index, lesson)
        # Prefer full dialog tracks (may be 1–2 files); fall back to activity audio.
        shadow_audio = list(activity.get("dialog_listen_audio") or activity.get("audio") or [])
        step.update(
            {
                "play_audio": shadow_audio[:2],
                "expect_speech": False,
                "auto_advance_after_audio": True,
                "instruction_en": "Shadow now — speak along quietly with the audio",
                "shadow_card": True,
                "say_target_jp": None,
                "dialog_script": activity.get("dialog_script") or [],
            }
        )
        # Force mode label for UI when standalone shadow_dialog
        if book_mode(activity) == "shadow_dialog":
            step["book_mode"] = "shadow_dialog"
        else:
            step["book_mode"] = book_mode(activity)
        return jp, en, step

    if sub == "repeat":
        p_idx = repeat_phrase_index(activity, quiz_index)
        if p_idx is not None and phrases:
            target = phrases[min(p_idx, len(phrases) - 1)]
            total = len(phrases)
            en = f"Listen and repeat ({p_idx + 1}/{total}) — say: {target}"
            alts: list[str] = []
        else:
            target = phrases[0] if phrases else ""
            en = f"Listen and repeat — say: {target}" if target else "Repeat the phrase from the CD."
            alts = phrases[1:4]
        jp = f"言いましょう。{target}" if target else "言いましょう。"
        step = _step_base(activity, sub, quiz_index, lesson)
        step.update(
            {
                "play_audio": [],
                "expect_speech": True,
                "auto_advance_after_audio": False,
                "instruction_en": "Repeat this phrase aloud",
                "say_target_jp": target or None,
                "say_alternates_jp": alts,
                "phrase_index": p_idx,
                "phrase_total": len(phrases) if p_idx is not None else None,
            }
        )
        return jp, en, step

    if sub == "select":
        target = phrases[0] if phrases else ""
        jp = "どんな あいさつ ですか。日本語で いってください。"
        en = activity.get("picture_hint_en") or "Which greeting fits the picture? Say it in Japanese."
        step = _step_base(activity, sub, quiz_index, lesson)
        step.update(
            {
                "play_audio": [],
                "expect_speech": True,
                "auto_advance_after_audio": False,
                "instruction_en": "Look at the picture in your book, then say the greeting",
                "picture_hint_en": activity.get("picture_hint_en"),
                "say_target_jp": target or None,
                "say_alternates_jp": phrases[1:4],
            }
        )
        return jp, en, step

    if sub in ("partner", "learner", "swap_partner", "swap_learner"):
        line = _dialog_line(activity, sub)
        text = (line or {}).get("jp") or (phrases[0] if phrases else "")
        is_tutor = sub in ("partner", "swap_partner")
        if sub == "swap_learner":
            en = "Roles swapped — you speak first (orange line in the book)."
        elif sub == "swap_partner":
            en = "Roles swapped — I speak the yellow (partner) line."
        elif is_tutor:
            en = "Dialog — yellow line (partner). You take orange next."
        else:
            en = "Your turn — orange line in the book."
        step = _step_base(activity, sub, quiz_index, lesson)
        step.update(
            {
                "play_audio": [],
                "expect_speech": not is_tutor,
                "auto_advance_after_audio": is_tutor,
                "dialog_line_jp": text,
                "dialog_speaker": "partner" if is_tutor else "learner",
                "book_line_color": "yellow" if is_tutor else "orange",
                "instruction_en": en,
                "say_target_jp": text if not is_tutor else None,
            }
        )
        jp = text if is_tutor else (f"あなたの セリフです。{text}" if text else "あなたの セリフを いってください。")
        return jp, en, step

    step = _step_base(activity, "repeat", quiz_index, lesson)
    step.update({"play_audio": [], "expect_speech": True, "auto_advance_after_audio": False})
    return "言いましょう。", "Say the phrase.", step


def book_section_intro(activity: dict) -> tuple[str, str] | None:
    jp = activity.get("book_section_jp")
    en = activity.get("book_section_en")
    if jp or en:
        return (jp or en or ""), (en or jp or "")
    return None


def expected_phrases_for_substep(activity: dict, quiz_index: int) -> list[str]:
    sub = substep_at(activity, quiz_index)
    phrases = _phrases(activity)
    if sub in ("learner", "swap_learner"):
        line = _dialog_line(activity, sub or "")
        # Accept dialog line + key_phrase alternates (kanji/kana variants).
        out: list[str] = []
        if line and line.get("jp"):
            out.append(line["jp"])
        for p in phrases:
            if p and p not in out:
                out.append(p)
        return out or phrases
    if sub in ("pronounce", "vocab_say", "select"):
        return phrases[:4] if phrases else []
    if sub == "repeat":
        p_idx = repeat_phrase_index(activity, quiz_index)
        if p_idx is not None and phrases:
            target = phrases[min(p_idx, len(phrases) - 1)]
            # Also accept other listed spellings of the same item when short list
            # is all alternates for one phrase (not listen_repeat_all drills).
            if book_mode(activity) != "listen_repeat_all":
                return [target] + [p for p in phrases if p != target]
            return [target]
    return phrases


def grammar_intro(lesson_id: str) -> tuple[str, str, dict]:
    pts = _grammar_for_lesson(lesson_id)
    if not pts:
        jp = "この れっすんに ぶんぽうシートは ありません。Can-do テストに いきます。"
        en = "No grammar worksheet for this lesson — moving to Can-do checks."
    else:
        jp = f"ぶんぽうの れんしゅう です。{len(pts)} こ あります。"
        en = f"Grammar worksheet — {len(pts)} items. Say the pattern or an example aloud."
    step = {
        "phase": "grammar",
        "play_audio": [],
        "audio": [],
        "expect_speech": bool(pts),
        "expects_speech": bool(pts),
        "auto_advance_after_audio": False,
        "auto_advance": False,
        "graded": False,
        "grammar_count": len(pts),
    }
    return jp, en, step


def grammar_item(point: dict, index: int, total: int) -> tuple[str, str, dict]:
    p = (point.get("point") or "")[:40]
    examples = point.get("examples") or []
    expected: list[str] = []
    for ex in examples:
        if isinstance(ex, dict) and ex.get("jp"):
            expected.append(str(ex["jp"]))
        elif isinstance(ex, str) and ex.strip():
            expected.append(ex.strip())
    jp = f"ぶんぽう {index + 1}。{p}。れいを いってみてください。"
    en = f"Grammar {index + 1}/{total}: {point.get('point')}"
    step = {
        "phase": "grammar",
        "play_audio": [],
        "audio": [],
        "expect_speech": True,
        "expects_speech": True,
        "auto_advance_after_audio": False,
        "auto_advance": False,
        "graded": False,
        "grammar_index": index,
        "grammar_total": total,
        "grammar_point": point.get("point"),
        "substep_index": index,
        "substep_total": total,
        "instruction_en": f"Grammar {index + 1} of {total} — say an example aloud",
        "expected_phrases": expected,
        "say_target_jp": expected[0] if expected else None,
    }
    return jp, en, step


def quiz_scenarios_for(lesson: dict, can_do_id: str) -> list[dict]:
    return [s for s in (lesson.get("quiz_scenarios") or []) if s.get("can_do_id") == can_do_id]


def pick_quiz_scenario(lesson: dict, can_do_id: str, attempt: int) -> dict | None:
    scenarios = quiz_scenarios_for(lesson, can_do_id)
    if not scenarios:
        return None
    return scenarios[attempt % len(scenarios)]


def quiz_step(can_do: dict, scenario: dict | None, *, expect_speech: bool) -> dict:
    expected = list((scenario or {}).get("expected") or [])
    if not expected and can_do:
        expected = list((can_do.get("rubric") or {}).get("must_include") or [])
    step: dict = {
        "phase": "quiz",
        "play_audio": [],
        "expect_speech": expect_speech,
        "auto_advance_after_audio": False,
        "can_do_id": can_do.get("id"),
        "book_substep": "reply",
    }
    if scenario:
        step["partner_jp"] = scenario.get("partner_jp")
        step["expected_phrases"] = expected
        step["instruction_en"] = scenario.get("hint_en") or "Reply in Japanese"
        step["say_target_jp"] = expected[0] if expected else None
        step["say_alternates_jp"] = expected[1:6]
        step["picture_hint_en"] = scenario.get("hint_en")
    return step


def quiz_prompt(can_do: dict, lesson: dict, scenario: dict | None = None) -> tuple[str, str, dict]:
    if scenario and scenario.get("partner_jp"):
        jp = str(scenario["partner_jp"])
        en = scenario.get("hint_en") or f"Reply in Japanese to: {jp}"
    else:
        stmt = can_do.get("statement_jp") or can_do.get("statement_en") or ""
        jp = f"Can-do テストです。{stmt[:50]}。 日本語で いってください。"
        en = f"Can-do check: {can_do.get('statement_en')}"
    step = quiz_step(can_do, scenario, expect_speech=True)
    return jp, en, step


def feedback_pass_short() -> str:
    return "よくできました。"


def feedback_retry(phrases: list[str]) -> str:
    if phrases:
        return f"もういちど。{'、'.join(phrases[:2])} いってください。"
    return "もういちど いってください。"


def lesson_complete_script() -> tuple[str, str]:
    return (
        "おつかれさまでした。この れっすん クリア です。つぎの れっすん へ いけます。",
        "Lesson complete. You can move to the next lesson.",
    )
