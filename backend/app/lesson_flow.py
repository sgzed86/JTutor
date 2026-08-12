"""Structured Irodori lesson flow — scripted A1 steps, no free-form teaching chat."""

from __future__ import annotations

import json
import re

from backend.app.book_modes import (
    activity_key_phrases,
    book_mode,
    fill_blank_index,
    flow_substeps,
    kanji_read_index,
    kanji_type_index,
    pronounce_phrase_index,
    repeat_phrase_index,
    spec_for,
    substep_at,
    vocab_phrase_index,
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
    acts.sort(key=lambda x: float(x.get("book_activity") or 0))
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
    return activity_key_phrases(activity)


def _blanks(activity: dict | None) -> list[dict]:
    if not activity:
        return []
    out: list[dict] = []
    for item in activity.get("blanks") or []:
        if isinstance(item, dict) and (item.get("prompt_jp") or "").strip():
            out.append(item)
    return out


def _choices_public(activity: dict | None) -> list[dict]:
    out: list[dict] = []
    for c in (activity or {}).get("choices") or []:
        if not isinstance(c, dict):
            continue
        cid = str(c.get("id") or "").strip()
        if not cid:
            continue
        item = {"id": cid}
        if c.get("label_jp"):
            item["label_jp"] = c["label_jp"]
        if c.get("label_en"):
            item["label_en"] = c["label_en"]
        out.append(item)
    return out


def _correct_ids(activity: dict | None) -> list[str]:
    return [str(x).strip() for x in ((activity or {}).get("correct_ids") or []) if str(x).strip()]


def parse_choice_ids(text: str) -> set[str]:
    parts = re.split(r"[,|、/\s]+", (text or "").strip())
    return {p.strip().lower() for p in parts if p.strip()}


def grade_choice_answer(text: str, activity: dict) -> dict:
    """Grade listen_choose / reading MCQ. `text` is comma-separated choice ids."""
    want = {x.lower() for x in _correct_ids(activity)}
    got = parse_choice_ids(text)
    mode = (activity.get("choose_mode") or ("all" if len(want) > 1 else "any")).lower()
    if not want:
        # No key — accept any non-empty selection.
        passed = bool(got)
    elif mode == "any":
        passed = bool(got & want)
    else:
        passed = got == want
    score = 100.0 if passed else (50.0 if got & want else 0.0)
    return {
        "passed": passed,
        "score": score,
        "similarity": score,
        "hits": sorted(got & want),
        "spoken": False,
        "feedback_jp": "よくできました。" if passed else "もういちど きいて、えらんでください。",
        "feedback_en": "Good!" if passed else "Listen again and choose carefully.",
        "best_match": ",".join(sorted(want)) if want else None,
    }


def grade_note_answer(text: str, activity: dict) -> dict:
    """Soft-grade notes: pass if non-empty; bonus if keywords appear."""
    body = (text or "").strip()
    keywords = [str(k).strip() for k in (activity.get("note_keywords") or []) if str(k).strip()]
    hits = [k for k in keywords if k and k in body]
    passed = len(body) >= 2
    score = 100.0 if hits else (80.0 if passed else 0.0)
    return {
        "passed": passed,
        "score": score,
        "similarity": score,
        "hits": hits,
        "spoken": False,
        "feedback_jp": "いい メモです。" if passed else "メモを かいてください。",
        "feedback_en": "Nice notes." if passed else "Type a short note about what you heard.",
        "best_match": hits[0] if hits else None,
    }


def _kanji_items(activity: dict | None) -> list[dict]:
    out: list[dict] = []
    for item in (activity or {}).get("kanji_items") or []:
        if isinstance(item, dict) and (item.get("kanji") or "").strip():
            out.append(item)
    return out


def grade_kanji_type(text: str, item: dict) -> dict:
    """Accept the kanji headword, or its reading as a soft alternative."""
    from backend.app.phrase_grade import grade_phrases, current_policy

    kanji = (item.get("kanji") or "").strip()
    reading = (item.get("reading") or "").strip()
    expected = [x for x in (kanji, reading) if x]
    grade = grade_phrases(text, expected, spoken=False, policy=current_policy())
    if not grade.get("passed") and reading and reading.replace(" ", "") in (text or "").replace(" ", ""):
        grade = {
            **grade,
            "passed": True,
            "score": 85.0,
            "feedback_jp": "読みは だいじょうぶ。できれば 漢字で かいてみましょう。",
            "feedback_en": "Reading is fine — try typing the kanji with your IME next time.",
            "best_match": reading,
        }
    elif grade.get("passed") and kanji and kanji in (text or ""):
        grade = {
            **grade,
            "feedback_jp": "よくできました。",
            "feedback_en": "Nice — that's the kanji.",
        }
    return grade


def _blank_slot_count(prompt_jp: str) -> int:
    return max(len(re.findall(r"＿+", prompt_jp or "")), 1)


def _fill_prompt(prompt_jp: str, fills: list[str]) -> str:
    parts = re.split(r"＿+", prompt_jp or "")
    out = parts[0] if parts else ""
    for i in range(len(parts) - 1):
        out += (fills[i] if i < len(fills) else "").strip()
        out += parts[i + 1] if i + 1 < len(parts) else ""
    return out


def expected_for_blank(blank: dict) -> list[str]:
    """Accepted answers for a cloze item (never sent to the client)."""
    out: list[str] = []
    full = (blank.get("full_jp") or "").strip()
    if full:
        out.append(full)
    answers = [str(a).strip() for a in (blank.get("answers") or []) if str(a).strip()]
    prompt = (blank.get("prompt_jp") or "").strip()
    if prompt and answers:
        filled = _fill_prompt(prompt, answers).strip()
        if filled and filled not in out:
            out.append(filled)
    if answers:
        joined = "".join(answers)
        if joined and joined not in out:
            out.append(joined)
        for a in answers:
            if a not in out:
                out.append(a)
    for alt in blank.get("answer_alts") or []:
        s = str(alt).strip()
        if s and s not in out:
            out.append(s)
    return out


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
    """Pick the dialog line for this substep.

    Book roles are fixed in the YAML: ``partner`` = yellow, ``learner`` = orange.
    On ``swap_*``, performers exchange lines, but ``book_speaker`` stays the
    original book role so yellow/orange colors never flip with the speakers.
    """
    lines = _dialog_lines(activity)
    if not lines:
        return None
    swap = substep.startswith("swap_")
    # Substep name is who performs now (partner/learner), not book color.
    want = "partner" if "partner" in substep else "learner"
    pool: list[dict] = []
    for ln in lines:
        book_speaker = ln.get("speaker") or "partner"
        performer = (
            ("learner" if book_speaker == "partner" else "partner") if swap else book_speaker
        )
        pool.append({**ln, "speaker": performer, "book_speaker": book_speaker})
    for ln in pool:
        if ln.get("speaker") == want:
            return ln
    first = lines[0]
    return {**first, "book_speaker": first.get("speaker") or "partner"}


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
        "expects_text": bool(spec and getattr(spec, "expects_text", False)),
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

    # Life & culture is always the quiet reflect card (including resumed listen slots).
    if sub == "listen" and book_mode(activity) == "culture_read":
        sub = "reflect"

    if sub == "listen":
        mode = book_mode(activity)
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
            en = activity.get("prompt_en") or "Vocabulary — listen to the CD, then say each word in Japanese."
            up_next = f"Next say: {phrases[0]}" if phrases else None
        elif mode == "pronunciation":
            jp = "はつおんに ちゅういして ききましょう。CDを きいてください。"
            en = activity.get("prompt_en") or "Pronunciation — listen for rhythm and long vowels, then repeat carefully."
            up_next = f"Next pronounce: {phrases[0]}" if phrases else None
        elif mode == "listen_choose":
            jp = "きいて、えらびましょう。CDを きいてください。"
            en = activity.get("prompt_en") or "Listen to the CD, then choose what you heard."
            up_next = "Next: tap the matching choice(s)."
        elif mode == "note_take":
            jp = "きいて、メモを かきましょう。CDを きいてください。"
            en = activity.get("prompt_en") or "Listen, then type brief notes about what you heard."
            up_next = "Next: type your notes."
        elif mode == "listen_repeat_all":
            jp = "聞いて、言いましょう。CDを きいてください。"
            n = len(phrases)
            en = (
                activity.get("prompt_en")
                or (f"Listen to the CD, then say each line one at a time ({n} lines)." if n else
                    "Listen to the CD, then repeat each phrase.")
            )
            up_next = f"Next you will say each line, starting with: {phrases[0]}" if phrases else None
        elif mode == "listen_fill":
            blanks = _blanks(activity)
            jp = "聞いて、空欄に 書きましょう。CDを きいてください。"
            n = len(blanks)
            en = (
                activity.get("prompt_en")
                or "Listen to the recording and fill in the blanks."
            )
            first = (blanks[0].get("prompt_jp") if blanks else "") or ""
            up_next = f"Next: type the missing words ({n} lines)." if n else None
            if first:
                up_next = f"Next fill in: {first}"
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
                "say_target_jp": phrases[0] if phrases and mode != "listen_fill" else None,
                "say_alternates_jp": phrases[1:4] if mode not in ("listen_repeat_all", "listen_fill") else [],
                "up_next_en": up_next,
                "phrase_total": len(phrases) if mode == "listen_repeat_all" else (
                    len(_blanks(activity)) if mode == "listen_fill" else None
                ),
            }
        )
        return jp, en, step

    if sub == "reflect":
        notes = (
            (activity.get("culture_notes_en") or "")
            or (lesson.get("english_notes") or "")
            or ""
        ).strip()
        # Quiet step: student reads in the book / on-screen; Yuki does not speak this.
        jp = ""
        en = "Life and culture — read this on your own when you like, then tap Next."
        step = _step_base(activity, sub, quiz_index)
        step.update(
            {
                "play_audio": [],
                "expect_speech": False,
                "auto_advance_after_audio": False,
                "auto_advance": False,
                "instruction_en": en,
                "book_mode": "culture_read",
                "culture_card": True,
                "culture_notes_en": notes[:1200] if notes else None,
                "passage_en": notes[:1200] if notes else None,
            }
        )
        return jp, en, step

    if sub == "read":
        passage_jp = (activity.get("passage_jp") or "").strip()
        passage_en = (activity.get("passage_en") or activity.get("prompt_en") or "").strip()
        jp = "よみましょう。"
        en = passage_en or "Read the passage in your book, then continue."
        step = _step_base(activity, sub, quiz_index, lesson)
        step.update(
            {
                "play_audio": [],
                "expect_speech": False,
                "auto_advance": False,
                "instruction_en": "Read carefully",
                "book_mode": "reading",
                "passage_jp": passage_jp or None,
                "passage_en": passage_en or None,
                "culture_notes_en": None,
            }
        )
        return jp, en, step

    if sub in ("choose", "read_check"):
        choices = _choices_public(activity)
        multi = (activity.get("choose_mode") or ("all" if len(_correct_ids(activity)) > 1 else "any")) == "all"
        expected_n = len(_correct_ids(activity)) or (1 if choices else 0)
        jp = "えらんでください。" if sub == "choose" else "しつもんに こたえてください。"
        en = (
            activity.get("prompt_en")
            or ("Choose every matching option." if multi else "Choose the best option.")
        )
        step = _step_base(activity, sub, quiz_index, lesson)
        step.update(
            {
                "play_audio": [],
                "expect_speech": False,
                "expects_speech": False,
                "expects_text": True,
                "auto_advance_after_audio": False,
                "instruction_en": en,
                "choices": choices,
                "choose_multi": multi,
                "choose_expected": expected_n or None,
                "passage_jp": activity.get("passage_jp"),
                "passage_en": activity.get("passage_en"),
                # Never expose correct_ids / note_keywords answers.
                "say_target_jp": None,
                "model_before_speech": False,
            }
        )
        return jp, en, step

    if sub == "note":
        jp = "メモを かいてください。"
        en = activity.get("prompt_en") or "Type brief notes about what you heard (who / what / where)."
        step = _step_base(activity, sub, quiz_index, lesson)
        step.update(
            {
                "play_audio": [],
                "expect_speech": False,
                "expects_speech": False,
                "expects_text": True,
                "auto_advance_after_audio": False,
                "instruction_en": en,
                "note_prompt_en": en,
                "expects_notes": True,
                "say_target_jp": None,
            }
        )
        return jp, en, step

    if sub == "kanji_study":
        items = _kanji_items(activity)
        jp = "漢字のことばを みましょう。"
        en = "Kanji words — check each character and its reading, then continue."
        step = _step_base(activity, sub, quiz_index, lesson)
        step.update(
            {
                "play_audio": [],
                "expect_speech": False,
                "auto_advance": False,
                "instruction_en": en,
                "book_mode": "kanji_words",
                "kanji_items": [
                    {
                        "kanji": it.get("kanji"),
                        "reading": it.get("reading"),
                        "gloss_en": it.get("gloss_en"),
                    }
                    for it in items
                ],
                "pdf_page": activity.get("pdf_page"),
            }
        )
        return jp, en, step

    if sub == "kanji_read":
        sentences = [s for s in (activity.get("kanji_sentences") or []) if str(s).strip()]
        focus_words = [
            str(it.get("kanji") or "").strip()
            for it in _kanji_items(activity)
            if str(it.get("kanji") or "").strip()
        ]
        r_idx = kanji_read_index(activity, quiz_index)
        total = len(sentences) or 1
        n = (r_idx + 1) if r_idx is not None else 1
        line = (
            sentences[min(r_idx, len(sentences) - 1)]
            if (r_idx is not None and sentences)
            else (sentences[0] if sentences else "")
        )
        # Book: read the underlined-kanji lines aloud, one at a time.
        jp = "この せんを よんでください。"
        en = (
            f"Read this line aloud ({n}/{total}), paying attention to the underlined kanji."
            if line
            else "Read the kanji example lines aloud."
        )
        step = _step_base(activity, sub, quiz_index, lesson)
        step.update(
            {
                "play_audio": [],
                "expect_speech": True,
                "expects_speech": True,
                "auto_advance": False,
                "instruction_en": en,
                "book_mode": "kanji_words",
                "kanji_sentences": sentences,
                "kanji_focus_words": focus_words,
                "kanji_read_index": r_idx,
                "kanji_read_total": total,
                "say_target_jp": line or None,
                "passage_jp": line or None,
                "model_before_speech": False,
            }
        )
        return jp, en, step

    if sub == "kanji_type":
        items = _kanji_items(activity)
        idx = kanji_type_index(activity, quiz_index)
        item = items[min(idx, len(items) - 1)] if (idx is not None and items) else (items[0] if items else {})
        kanji = (item.get("kanji") or "").strip()
        reading = (item.get("reading") or "").strip()
        gloss = (item.get("gloss_en") or "").strip()
        total = len(items) or 1
        n = (idx + 1) if idx is not None else 1
        jp = "キーボードで にゅうりょく してください。"
        en = f"Type this word ({n}/{total})" + (f" — {gloss}" if gloss else "")
        step = _step_base(activity, sub, quiz_index, lesson)
        step.update(
            {
                "play_audio": [],
                "expect_speech": False,
                "expects_speech": False,
                "expects_text": True,
                "auto_advance": False,
                "instruction_en": en,
                "book_mode": "kanji_words",
                "kanji_prompt": {
                    "kanji": kanji or None,
                    "reading": reading or None,
                    "gloss_en": gloss or None,
                    "index": idx,
                    "total": total,
                },
                # Hint with reading; do not require revealing answer key beyond that.
                "say_target_jp": None,
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
        p_idx = pronounce_phrase_index(activity, quiz_index)
        if p_idx is not None and phrases:
            target = phrases[min(p_idx, len(phrases) - 1)]
        else:
            target = phrases[0] if phrases else ""
        jp = "はつおんを たしかに いってください。"
        en = f"Pronunciation — say clearly (watch long vowels): {target}" if target else "Say the phrase clearly."
        step = _step_base(activity, sub, quiz_index)
        step.update(
            {
                "play_audio": [],
                "expect_speech": True,
                "auto_advance_after_audio": False,
                "instruction_en": "Focus on mora and long vowels",
                "say_target_jp": target or None,
                "say_alternates_jp": [],
                "book_mode": "pronunciation",
                "model_before_speech": True,
                "phrase_index": p_idx,
                "phrase_total": len(phrases) if phrases else None,
            }
        )
        return jp, en, step

    if sub == "vocab_say":
        p_idx = vocab_phrase_index(activity, quiz_index)
        if p_idx is not None and phrases:
            target = phrases[min(p_idx, len(phrases) - 1)]
        else:
            target = phrases[0] if phrases else ""
        gloss_map = activity.get("glosses_en") or {}
        gloss = (
            (gloss_map.get(target) if isinstance(gloss_map, dict) else None)
            or (activity.get("vocab_gloss_en") or activity.get("gloss_en") or "")
        )
        gloss = str(gloss or "").strip()
        jp = "ことばを いってください。"
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
                "model_before_speech": True,
                "phrase_index": p_idx,
                "phrase_total": len(phrases) if phrases else None,
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
        # Keep the coach line short; the client TTS-models `say_target_jp` clearly.
        jp = "言いましょう。"
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
                "model_before_speech": True,
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
                "model_before_speech": True,
            }
        )
        return jp, en, step

    if sub in ("partner", "learner", "swap_partner", "swap_learner"):
        line = _dialog_line(activity, sub)
        text = (line or {}).get("jp") or (phrases[0] if phrases else "")
        is_tutor = sub in ("partner", "swap_partner")
        # Yellow/orange follow the book line, not who is speaking this pass.
        book_speaker = (line or {}).get("book_speaker") or (line or {}).get("speaker") or "partner"
        line_color = "yellow" if book_speaker == "partner" else "orange"
        # Keep Yuki's yellow question on screen while the learner answers (conversation).
        yellow_text = ""
        if sub == "learner":
            yellow_line = _dialog_line(activity, "partner")
            yellow_text = (yellow_line or {}).get("jp") or ""
        if sub == "swap_learner":
            en = "Roles swapped — you speak first (yellow line in the book)."
        elif sub == "swap_partner":
            en = "Roles swapped — I speak the orange line."
        elif is_tutor:
            en = "Dialog — yellow line (partner). You take orange next."
        else:
            en = "Your turn — reply with the orange line."
        step = _step_base(activity, sub, quiz_index, lesson)
        step.update(
            {
                "play_audio": [],
                "expect_speech": not is_tutor,
                "auto_advance_after_audio": is_tutor,
                "dialog_line_jp": text,
                "dialog_speaker": "partner" if is_tutor else "learner",
                "book_line_color": line_color,
                "instruction_en": en,
                "say_target_jp": text if not is_tutor else None,
                # Conversation role-play: never TTS-model the learner's line.
                "model_before_speech": False,
                # Pass 1: leave Yuki's yellow line visible while you answer orange.
                "partner_jp": yellow_text if sub == "learner" else None,
            }
        )
        # Yuki only speaks her character lines (yellow pass 1 / orange pass 2).
        # Learner turns stay silent so it feels like a real exchange, not drill.
        if is_tutor:
            jp = text
        elif sub == "swap_learner":
            jp = "じゃ、かわりましょう。"
        else:
            jp = ""
        return jp, en, step

    if sub == "fill":
        blanks = _blanks(activity)
        b_idx = fill_blank_index(activity, quiz_index)
        blank = blanks[min(b_idx, len(blanks) - 1)] if (b_idx is not None and blanks) else (
            blanks[0] if blanks else {}
        )
        prompt = (blank.get("prompt_jp") or "").strip()
        slots = _blank_slot_count(prompt)
        total = len(blanks) or 1
        index_1 = (b_idx + 1) if b_idx is not None else 1
        jp = "空欄に ことばを 書いてください。"
        en = f"Fill in the blank ({index_1}/{total}) — type what you heard."
        step = _step_base(activity, sub, quiz_index, lesson)
        step.update(
            {
                "play_audio": [],
                "expect_speech": False,
                "expects_speech": False,
                "expects_text": True,
                "auto_advance_after_audio": False,
                "instruction_en": "Listen again if you need to, then type the missing word(s).",
                "blank_prompt_jp": prompt or None,
                "blank_count": slots,
                "blank_index": b_idx,
                "blank_total": total,
                # Do not expose answers / full_jp to the client.
                "say_target_jp": None,
                "model_before_speech": False,
            }
        )
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
        if sub == "vocab_say":
            p_idx = vocab_phrase_index(activity, quiz_index)
            if p_idx is not None and phrases:
                return [phrases[min(p_idx, len(phrases) - 1)]]
        if sub == "pronounce":
            p_idx = pronounce_phrase_index(activity, quiz_index)
            if p_idx is not None and phrases:
                return [phrases[min(p_idx, len(phrases) - 1)]]
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
    if sub == "fill":
        blanks = _blanks(activity)
        b_idx = fill_blank_index(activity, quiz_index)
        if b_idx is not None and blanks:
            blank = blanks[min(b_idx, len(blanks) - 1)]
            return expected_for_blank(blank)
        return expected_for_blank(blanks[0]) if blanks else phrases
    if sub == "kanji_read":
        sentences = [s for s in (activity.get("kanji_sentences") or []) if str(s).strip()]
        r_idx = kanji_read_index(activity, quiz_index)
        if r_idx is not None and sentences:
            return [sentences[min(r_idx, len(sentences) - 1)]]
        return sentences[:1]
    return phrases


def _grammar_examples(point: dict) -> list[str]:
    expected: list[str] = []
    for ex in point.get("examples") or []:
        if isinstance(ex, dict) and ex.get("jp"):
            expected.append(str(ex["jp"]).strip())
        elif isinstance(ex, str) and ex.strip():
            expected.append(ex.strip())
    return [e for e in expected if e]


def _is_worksheet_grammar_point(point: dict) -> bool:
    """Keep curated points; drop OCR dialogue debris with nothing to practice."""
    if not isinstance(point, dict):
        return False
    if any(isinstance(e, dict) for e in (point.get("exercises") or [])):
        return True
    if _grammar_examples(point):
        return True
    text = (point.get("point") or "").strip()
    if not text:
        return False
    # Dialogue / emoji OCR leftovers from worksheet scans.
    if re.search(r"[😞😄]", text):
        return False
    if text.startswith(("A：", "A:", "B：", "B:")):
        return False
    if "→（" in text or "→(" in text:
        return False
    # Pattern-like labels (N です, V-て, 〜ます) still open the worksheet page.
    if re.search(r"(です|ます|じゃない|〜|N\b|V-|イ\s*A|ナ\s*A|【)", text):
        return True
    # Bare truncated dialogue fragments without examples — skip.
    if len(text) > 24 and ("？" in text or "?" in text):
        return False
    return len(text) <= 24


def grammar_turns(ex: dict) -> list[dict]:
    """Expand one workbook exercise into dialogue turns (listen / fill / choose)."""
    raw = [t for t in (ex.get("turns") or []) if isinstance(t, dict)]
    if raw:
        out: list[dict] = []
        for t in raw:
            kind = (t.get("kind") or "").strip().lower()
            if kind not in ("listen", "fill", "choose"):
                if t.get("choices"):
                    kind = "choose"
                elif t.get("blank_prompt_jp") or t.get("answers") or t.get("line_jp"):
                    kind = "fill"
                else:
                    kind = "listen"
            out.append({**t, "kind": kind})
        return out

    # Legacy flat exercise → listen (optional) + fill/choose + follow listen (optional).
    turns: list[dict] = []
    partner = (ex.get("partner_jp") or "").strip()
    read_jp = (ex.get("read_jp") or "").strip()
    follow = (ex.get("follow_jp") or "").strip()
    if partner and (ex.get("blank_prompt_jp") or ex.get("choices") or ex.get("answers")):
        turns.append({"kind": "listen", "jp": partner, "role": "A"})
    if ex.get("choices"):
        turns.append(
            {
                "kind": "choose",
                "role": "B",
                "partner_jp": None if partner else read_jp or None,
                "read_jp": None if partner else read_jp or None,
                "instruction_en": ex.get("instruction_en"),
                "choices": ex.get("choices") or [],
                "correct_ids": ex.get("correct_ids") or [],
                "choose_multi": bool(ex.get("choose_multi")),
            }
        )
    elif ex.get("blank_prompt_jp") or ex.get("answers") or ex.get("line_jp") or ex.get("expected"):
        turns.append(
            {
                "kind": "fill",
                "role": "B" if partner else "A",
                "cue_jp": ex.get("cue_jp"),
                "blank_prompt_jp": ex.get("blank_prompt_jp"),
                "line_jp": ex.get("line_jp"),
                "read_jp": None if partner else read_jp or None,
                "instruction_en": ex.get("instruction_en"),
                "answers": ex.get("answers") or [],
                "full_jp": ex.get("full_jp"),
                "answer_alts": ex.get("answer_alts") or [],
                "expected": ex.get("expected") or [],
            }
        )
    elif partner or read_jp:
        turns.append({"kind": "listen", "jp": partner or read_jp})
    if follow:
        turns.append({"kind": "listen", "jp": follow})
    return turns


def grammar_drills(lesson_id: str) -> list[dict]:
    """Flatten grammar points into drills (each workbook turn/line is one step)."""
    drills: list[dict] = []
    for point in _grammar_for_lesson(lesson_id):
        if not _is_worksheet_grammar_point(point):
            continue
        exercises = [e for e in (point.get("exercises") or []) if isinstance(e, dict)]
        base = {
            "point": (point.get("point") or "").strip(),
            "pattern_en": (point.get("pattern_en") or point.get("point") or "").strip(),
            "prompt_jp": (point.get("prompt_jp") or "").strip(),
            "prompt_en": (point.get("prompt_en") or "").strip(),
            "examples": point.get("examples") or [],
            "worksheet_pages": point.get("worksheet_pages") or [],
        }
        if exercises:
            for ex_i, ex in enumerate(exercises):
                turns = grammar_turns(ex)
                if not turns:
                    drills.append(
                        {
                            **base,
                            "exercise": ex,
                            "turn": None,
                            "exercise_index": ex_i,
                            "turn_index": 0,
                            "facilitate": True,
                        }
                    )
                    continue
                for ti, turn in enumerate(turns):
                    drills.append(
                        {
                            **base,
                            "exercise": ex,
                            "turn": turn,
                            "exercise_index": ex_i,
                            "turn_index": ti,
                            "facilitate": True,
                        }
                    )
        else:
            # No facilitate turns: walk every example line (worksheet practice lines).
            example_lines = _grammar_examples(point)
            if example_lines:
                for ei, line in enumerate(example_lines):
                    drills.append(
                        {
                            **base,
                            "examples": [{"jp": line}],
                            "example_index": ei,
                            "example_total": len(example_lines),
                            "exercise": None,
                            "turn": None,
                            "exercise_index": 0,
                            "turn_index": 0,
                            "facilitate": False,
                        }
                    )
            else:
                drills.append(
                    {
                        **base,
                        "exercise": None,
                        "turn": None,
                        "exercise_index": 0,
                        "turn_index": 0,
                        "facilitate": False,
                    }
                )
    return drills


def grammar_active(drill: dict) -> dict:
    """The turn being practiced, falling back to a flat exercise dict."""
    turn = drill.get("turn") if isinstance(drill.get("turn"), dict) else None
    if turn:
        return turn
    ex = drill.get("exercise") if isinstance(drill.get("exercise"), dict) else None
    return ex or {}


def grammar_blank(ex: dict) -> dict:
    """Normalize a grammar fill turn into a cloze blank dict for grading/UI."""
    cue = (ex.get("cue_jp") or "").strip()
    prompt = (ex.get("blank_prompt_jp") or "").strip()
    if not prompt:
        line = (ex.get("line_jp") or "").strip()
        if line and "＿" in line:
            prompt = line
        elif line and cue and f"（{cue}）" in line:
            prompt = line.replace(f"（{cue}）", "＿")
        elif line:
            prompt = re.sub(r"（[^）]+）", "＿", line)
        else:
            prompt = "＿"
    answers = [str(a).strip() for a in (ex.get("answers") or []) if str(a).strip()]
    full = (ex.get("full_jp") or "").strip()
    alts = [str(a).strip() for a in (ex.get("answer_alts") or []) if str(a).strip()]
    legacy = [str(a).strip() for a in (ex.get("expected") or []) if str(a).strip()]
    if not answers and legacy:
        # Prefer a short fill over a full-line legacy expected when possible.
        shell = prompt.replace("＿", "").strip()
        short = [e for e in legacy if e and e not in shell and (not full or e != full)]
        answers = [min(short, key=len)] if short else [legacy[-1]]
        if not full:
            full = legacy[0]
    for e in legacy:
        if e and e not in alts:
            alts.append(e)
    return {
        "prompt_jp": prompt,
        "answers": answers,
        "full_jp": full or None,
        "answer_alts": alts,
        "cue_jp": cue or None,
    }


def grammar_is_choose(ex: dict | None) -> bool:
    if not ex:
        return False
    if (ex.get("kind") or "").strip().lower() == "choose":
        return True
    return bool(ex.get("choices") or [])


def grammar_is_listen(ex: dict | None) -> bool:
    if not ex:
        return False
    kind = (ex.get("kind") or "").strip().lower()
    if kind == "listen":
        return True
    if kind in ("fill", "choose"):
        return False
    # Flat leftover with only jp and no learner task.
    return bool((ex.get("jp") or "").strip()) and not ex.get("choices") and not (
        ex.get("blank_prompt_jp") or ex.get("answers") or ex.get("line_jp")
    )


def grammar_expected(drill: dict) -> list[str]:
    """Answers used for grading — never shown as the on-screen target in facilitate mode."""
    active = grammar_active(drill)
    if grammar_is_listen(active):
        return []
    if grammar_is_choose(active):
        return [str(x).strip() for x in (active.get("correct_ids") or []) if str(x).strip()]
    if active:
        return expected_for_blank(grammar_blank(active))
    return _grammar_examples(drill)


def grammar_intro(lesson_id: str) -> tuple[str, str, dict]:
    drills = grammar_drills(lesson_id)
    if not drills:
        jp = "この れっすんに ぶんぽうシートは ありません。Can-do テストに いきます。"
        en = "No grammar worksheet for this lesson — moving to Can-do checks."
    else:
        jp = f"ぶんぽうの れんしゅう です。{len(drills)} こ あります。ワークシートを みてください。"
        en = (
            f"Grammar worksheet — {len(drills)} lines. "
            "We will go through each line: I read fixed lines; you type blanks, choose, or say examples."
        )
    step = {
        "phase": "grammar",
        "play_audio": [],
        "audio": [],
        "expect_speech": False,
        "expects_speech": False,
        "auto_advance_after_audio": False,
        "auto_advance": False,
        "graded": False,
        "grammar_count": len(drills),
        "instruction_en": en,
    }
    return jp, en, step


def grammar_item(drill: dict, index: int, total: int) -> tuple[str, str, dict]:
    """One grammar drill. Facilitate mode: Yuki reads fixed lines; learner fills/chooses."""
    pattern = (drill.get("point") or "").strip()
    pattern_en = (drill.get("pattern_en") or pattern).strip()
    expected = grammar_expected(drill)
    facilitate = bool(drill.get("facilitate") and (drill.get("turn") or drill.get("exercise")))
    active = grammar_active(drill)
    parent = drill.get("exercise") if isinstance(drill.get("exercise"), dict) else {}
    role = (active.get("role") or "").strip().upper()

    if facilitate and grammar_is_listen(active):
        line = (active.get("jp") or active.get("partner_jp") or active.get("read_jp") or "").strip()
        instruction = (
            (active.get("instruction_en") or "").strip()
            or (parent.get("instruction_en") or "").strip()
            or f"Grammar {index + 1}/{total} — listen to this line."
        )
        if role:
            instruction = f"{instruction} (Speaker {role})"
        jp = line or "きいてください。"
        step = {
            "phase": "grammar",
            "play_audio": [],
            "audio": [],
            "expect_speech": False,
            "expects_speech": False,
            "expects_text": False,
            "auto_advance_after_audio": True,
            "auto_advance": True,
            "graded": False,
            "grammar_index": index,
            "grammar_total": total,
            "grammar_point": pattern,
            "grammar_pattern_en": pattern_en,
            "substep_index": index,
            "substep_total": total,
            "instruction_en": instruction,
            "expected_phrases": [],
            "say_target_jp": None,
            "say_alternates_jp": [],
            "dialog_line_jp": line or None,
            "passage_jp": line or None,
            "partner_jp": line or None,
            "book_substep": "grammar_listen",
            "model_before_speech": False,
            "facilitate": True,
            "grammar_role": role or None,
        }
        return jp, instruction, step

    if facilitate and grammar_is_choose(active):
        partner = (active.get("partner_jp") or "").strip()
        read_jp = (active.get("read_jp") or "").strip()
        instruction = (
            (active.get("instruction_en") or "").strip()
            or (parent.get("instruction_en") or "").strip()
            or (drill.get("prompt_en") or "").strip()
            or f"Grammar {index + 1}/{total} ({pattern_en}) — choose the correct answer."
        )
        jp = partner or read_jp or "えらんでください。"
        choices = []
        for c in active.get("choices") or []:
            if not isinstance(c, dict) or not c.get("id"):
                continue
            choices.append(
                {
                    "id": str(c["id"]),
                    "label_jp": c.get("label_jp"),
                    "label_en": c.get("label_en"),
                }
            )
        step = {
            "phase": "grammar",
            "play_audio": [],
            "audio": [],
            "expect_speech": False,
            "expects_speech": False,
            "expects_text": True,
            "auto_advance_after_audio": False,
            "auto_advance": False,
            "graded": True,
            "grammar_index": index,
            "grammar_total": total,
            "grammar_point": pattern,
            "grammar_pattern_en": pattern_en,
            "substep_index": index,
            "substep_total": total,
            "instruction_en": instruction,
            "expected_phrases": expected,
            "say_target_jp": None,
            "say_alternates_jp": [],
            "choices": choices,
            "choose_multi": bool(active.get("choose_multi")),
            "partner_jp": partner or None,
            "book_substep": "grammar_choose",
            "model_before_speech": False,
            "facilitate": True,
            "grammar_role": role or None,
        }
        return jp, instruction, step

    if facilitate:
        blank = grammar_blank(active)
        cue = (blank.get("cue_jp") or "").strip()
        prompt = (blank.get("prompt_jp") or "＿").strip()
        partner = (active.get("partner_jp") or "").strip()
        read_jp = (active.get("read_jp") or "").strip()
        instruction = (
            (active.get("instruction_en") or "").strip()
            or (parent.get("instruction_en") or "").strip()
            or (drill.get("prompt_en") or "").strip()
            or f"Grammar {index + 1}/{total} ({pattern_en}) — type the missing part."
        )
        prompt_jp = (drill.get("prompt_jp") or "").strip()
        if partner:
            jp = partner
        elif read_jp:
            jp = read_jp
        elif cue:
            jp = f"{prompt_jp} {cue}".strip() if prompt_jp else cue
        else:
            jp = "空欄に ことばを 書いてください。"
        en = instruction
        slots = _blank_slot_count(prompt)
        step = {
            "phase": "grammar",
            "play_audio": [],
            "audio": [],
            "expect_speech": False,
            "expects_speech": False,
            "expects_text": True,
            "auto_advance_after_audio": False,
            "auto_advance": False,
            "graded": True,
            "grammar_index": index,
            "grammar_total": total,
            "grammar_point": pattern,
            "grammar_pattern_en": pattern_en,
            "substep_index": index,
            "substep_total": total,
            "instruction_en": instruction,
            "expected_phrases": expected,
            "say_target_jp": None,
            "say_alternates_jp": [],
            "blank_prompt_jp": prompt,
            "blank_count": slots,
            "blank_index": index,
            "blank_total": total,
            "grammar_cue_jp": cue or None,
            "partner_jp": partner or None,
            "book_substep": "grammar_fill",
            "model_before_speech": False,
            "facilitate": True,
            "grammar_role": role or None,
        }
        return jp, en, step

    target = expected[0] if expected else None
    prompt_en = (drill.get("prompt_en") or "").strip()
    prompt_jp = (drill.get("prompt_jp") or "").strip()
    # Strip leaked answer tails like 「れい：…」 / 「Say: …」 from older prompts.
    prompt_jp = re.split(r"[。．]?\s*れい[：:]", prompt_jp, maxsplit=1)[0].strip(" 。．")
    prompt_en = re.split(r"\s*[—-]\s*say\b|\s+Say:\s*", prompt_en, maxsplit=1, flags=re.I)[0].strip(" .")
    example_i = drill.get("example_index")
    example_n = drill.get("example_total")

    if target:
        jp = prompt_jp or f"ぶんぽう {index + 1}。つぎを いってください。"
        if example_i is not None and example_n:
            en = (
                f"Grammar worksheet line {index + 1}/{total} ({pattern_en}) — "
                f"say example {int(example_i) + 1} of {int(example_n)}."
            )
            instruction = en
        else:
            en = prompt_en or f"Grammar {index + 1}/{total} ({pattern_en})."
            instruction = prompt_en or f"Grammar {index + 1}/{total} ({pattern_en}) — say the line."
    else:
        jp = f"ぶんぽう {index + 1}。{pattern}。ワークシートを みてください。"
        en = (
            f"Grammar {index + 1}/{total}: {pattern_en}. "
            "Look at this pattern in your grammar worksheet, then tap Next."
        )
        instruction = en

    step = {
        "phase": "grammar",
        "play_audio": [],
        "audio": [],
        "expect_speech": bool(target),
        "expects_speech": bool(target),
        "auto_advance_after_audio": False,
        "auto_advance": False,
        "graded": bool(target),
        "grammar_index": index,
        "grammar_total": total,
        "grammar_point": pattern,
        "grammar_pattern_en": pattern_en,
        "substep_index": index,
        "substep_total": total,
        "instruction_en": instruction,
        "expected_phrases": expected,
        "say_target_jp": target,
        "say_alternates_jp": expected[1:4],
        "book_substep": "grammar_say" if target else "grammar_read",
        # Do not pre-speak the answer; learner produces it.
        "model_before_speech": False,
        "facilitate": False,
    }
    return jp, en, step


_WEAK_QUIZ_PARTNERS = {
    "では、お願いします。",
    "もう一度、お願いします。",
    "こんにちは。",
    "ちち。",
    "ちちです。",
}

_DEFAULT_ROLEPLAY_OPENER = "じゃあ、やってみましょう。"


def quiz_scenarios_for(lesson: dict, can_do_id: str) -> list[dict]:
    return [s for s in (lesson.get("quiz_scenarios") or []) if s.get("can_do_id") == can_do_id]


def _scenario_rank(scenario: dict) -> tuple[int, int]:
    """Prefer real role-plays over bare keyword prompts."""
    partner = (scenario.get("partner_jp") or "").strip()
    if scenario.get("setup_en") or scenario.get("goal_en"):
        quality = 0
    elif partner in _WEAK_QUIZ_PARTNERS:
        quality = 2
    else:
        quality = 1
    return (quality, len(partner))


def pick_quiz_scenario(lesson: dict, can_do_id: str, attempt: int) -> dict | None:
    scenarios = quiz_scenarios_for(lesson, can_do_id)
    if not scenarios:
        return None
    ranked = sorted(scenarios, key=_scenario_rank)
    # Rotate within the best quality band first.
    best = _scenario_rank(ranked[0])[0]
    band = [s for s in ranked if _scenario_rank(s)[0] == best]
    return band[attempt % len(band)]


def enrich_quiz_scenario(can_do: dict | None, scenario: dict | None) -> dict:
    """Fill setup/goal (and weak openers) so every Can-do is a real role-play check."""
    cd = can_do or {}
    out = dict(scenario or {})
    stmt_en = (cd.get("statement_en") or "").strip()
    hint = (out.get("hint_en") or "").strip()
    setup = (out.get("setup_en") or "").strip()
    if not setup:
        if hint.lower().startswith("situation:"):
            setup = hint.split(":", 1)[1].strip()
            for noise in (
                " Reply using lesson phrases.",
                " Reply using lesson phrases",
            ):
                if setup.endswith(noise):
                    setup = setup[: -len(noise)].strip()
        elif hint and not hint.lower().startswith("again"):
            setup = hint
        elif stmt_en:
            setup = f"Role-play — show that you can: {stmt_en}"
        else:
            setup = "Role-play — reply to Yuki in Japanese."
    out["setup_en"] = setup
    if not (out.get("goal_en") or "").strip():
        out["goal_en"] = (
            f"Learner demonstrates: {stmt_en}"
            if stmt_en
            else "Learner communicates the can-do intent in Japanese."
        )
    partner = (out.get("partner_jp") or "").strip()
    if not partner or partner in _WEAK_QUIZ_PARTNERS:
        out["partner_jp"] = _DEFAULT_ROLEPLAY_OPENER
    expected = out.get("expected") or []
    if not expected:
        expected = list((cd.get("rubric") or {}).get("must_include") or [])
    # YAML may parse bare digits as ints — grading expects strings.
    out["expected"] = [str(x) for x in expected if x is not None and str(x).strip()]
    out["can_do_id"] = out.get("can_do_id") or cd.get("id")
    return out


def quiz_step(can_do: dict, scenario: dict | None, *, expect_speech: bool) -> dict:
    scenario = enrich_quiz_scenario(can_do, scenario)
    expected = list(scenario.get("expected") or [])
    if not expected and can_do:
        expected = list((can_do.get("rubric") or {}).get("must_include") or [])
    setup = (scenario.get("setup_en") or "").strip()
    step: dict = {
        "phase": "quiz",
        "play_audio": [],
        "expect_speech": expect_speech,
        "expects_speech": expect_speech,
        "auto_advance_after_audio": False,
        "can_do_id": can_do.get("id"),
        "statement_en": can_do.get("statement_en"),
        "statement_jp": can_do.get("statement_jp"),
        "book_substep": "roleplay",
        "book_mode": "dialog",
        # Never reveal acceptable answers on the stage.
        "say_target_jp": None,
        "say_alternates_jp": [],
        "model_before_speech": False,
        "partner_jp": scenario.get("partner_jp"),
        # Kept for server/harness grading only — UI must not surface these as a target.
        "expected_phrases": expected,
        "instruction_en": setup or "Role-play — reply in Japanese.",
        "picture_hint_en": setup,
        "goal_en": scenario.get("goal_en"),
    }
    return step


def quiz_prompt(can_do: dict, lesson: dict, scenario: dict | None = None) -> tuple[str, str, dict]:
    scenario = enrich_quiz_scenario(can_do, scenario)
    jp = str(scenario.get("partner_jp") or _DEFAULT_ROLEPLAY_OPENER)
    en = scenario.get("setup_en") or f"Role-play check: {can_do.get('statement_en')}"
    step = quiz_step(can_do, scenario, expect_speech=True)
    return jp, en, step


def feedback_pass_short() -> str:
    return "よくできました。"


def feedback_retry(phrases: list[str]) -> str:
    if phrases:
        return f"もういちど。{'、'.join(phrases[:2])} いってください。"
    return "もういちど いってください。"


def feedback_retry_choice() -> str:
    """Spoken after a miss — do not model the target; the UI offers recovery choices."""
    return "ちょっとちがいます。どうしますか？"


def feedback_retry_choice_en() -> str:
    return "Not quite — hear the recording, hear Yuki say it, or try again."


def lesson_complete_script() -> tuple[str, str]:
    return (
        "おつかれさまでした。この れっすん クリア です。つぎの れっすん へ いけます。",
        "Lesson complete. You can move to the next lesson.",
    )
