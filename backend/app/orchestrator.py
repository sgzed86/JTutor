"""Structured tutor: book exercises → grammar → Can-do tests (A1-simple Japanese)."""

from __future__ import annotations

import json
from datetime import datetime

from sqlalchemy.orm import Session

from backend.app import lesson_flow as flow
from backend.app import ollama_client
from backend.app import srs_service
from backend.app.book_modes import flow_substeps, speech_substeps, substep_at
from backend.app.config import settings
from backend.app.curriculum_loader import load_lesson, list_lessons
from backend.app.db import CanDoProgress, ChatSession, LessonProgress
from backend.app.free_response import acknowledge_intro, intro_questions, intro_step
from backend.app.lesson_access import locked_response
from backend.app.lesson_progress import lesson_progress_snapshot
from backend.app.lesson_unlock import is_lesson_unlocked, next_lesson_id
from backend.app.logging_setup import log_event
from backend.app.phrase_grade import grade_phrases, normalize_jp_for_grade, quiz_grade
from backend.app.self_check import save_self_check, self_check_step, self_check_summary


def _apply_mastery_gate(grade: dict) -> dict:
    score = float(grade.get("score") or 0)
    grade["passed"] = bool(grade.get("passed")) and score >= settings.mastery_min_score
    return grade


def _outstanding_can_dos(db: Session, lesson: dict) -> list[dict]:
    pending: list[dict] = []
    for c in lesson.get("can_dos") or []:
        row = db.get(CanDoProgress, c["id"])
        if not row or not row.mastered:
            pending.append(c)
    return pending


def _announce_can_do_retry(db: Session, session: ChatSession, lesson: dict, messages: list[dict]) -> None:
    pending = _outstanding_can_dos(db, lesson)
    labels = [c.get("statement_en") or c.get("id") or "" for c in pending[:4]]
    en_list = "; ".join(labels) if labels else "see Progress map"
    jp = "まだ Can-do が ぜんぶ クリア ではありません。もういちど れんしゅう しましょう。"
    en = f"Not all Can-do checks are mastered yet ({len(pending)} remaining). Still need: {en_list}"
    _append_tutor(
        messages,
        jp,
        en,
        {"phase": "quiz", "help": True, "expect_speech": False, "play_audio": []},
        session.state,
    )


def _activity_by_id(lesson: dict, activity_id: str | None) -> dict | None:
    if not activity_id:
        return None
    for a in lesson.get("activities") or []:
        if a.get("id") == activity_id:
            return a
    return None


def _msgs(session: ChatSession) -> list[dict]:
    try:
        return json.loads(session.messages_json or "[]")
    except json.JSONDecodeError:
        return []


def _save_msgs(session: ChatSession, messages: list[dict]) -> None:
    session.messages_json = json.dumps(messages, ensure_ascii=False)
    session.updated_at = datetime.utcnow()


def _append_tutor(
    messages: list[dict],
    jp: str,
    en: str,
    step: dict,
    state: str,
) -> None:
    messages.append(
        {
            "role": "assistant",
            "content": jp,
            "hint_en": en,
            "step": step,
            "state": state,
        }
    )


def _sync_book_substep(session: ChatSession, messages: list[dict]) -> None:
    """Align quiz_index with the latest assistant step (fixes resumed / legacy sessions)."""
    if session.state != "book" or not messages:
        return
    last_a = None
    for m in reversed(messages):
        if m.get("role") != "assistant":
            continue
        st = m.get("step") or {}
        if st.get("help"):
            continue
        last_a = m
        break
    if not last_a:
        return
    st = last_a.get("step") or {}
    if st.get("book_flow_index") is not None:
        session.quiz_index = int(st["book_flow_index"])
        return
    sub = st.get("book_substep")
    if sub == "practice":
        session.quiz_index = 1
    elif sub == "announce":
        session.quiz_index = 0
    elif st.get("expect_speech") and not (st.get("play_audio") or []):
        session.quiz_index = max(session.quiz_index, 1)


def _book_emit_step(
    session: ChatSession,
    lesson: dict,
    activity: dict,
    messages: list[dict],
    quiz_index: int,
) -> dict:
    session.quiz_index = quiz_index
    jp, en, step = flow.book_step(activity, lesson, quiz_index)
    _append_tutor(messages, jp, en, step, session.state)
    return step


def _book_advance_substep_or_track(
    session: ChatSession,
    lesson: dict,
    messages: list[dict],
    activity: dict | None,
) -> dict:
    """Next sub-step within the activity, or next track / grammar."""
    if not activity:
        return _begin_grammar(session, lesson, messages)
    subs = flow_substeps(activity)
    nxt = session.quiz_index + 1
    if nxt < len(subs):
        return _book_emit_step(session, lesson, activity, messages, nxt)
    session.quiz_index = 0
    if _next_book_track(session, lesson):
        return _begin_book_track(session, lesson, messages)
    return _begin_grammar(session, lesson, messages)


def _resolve_step(
    session: ChatSession,
    lesson: dict,
    activity: dict | None,
    messages: list[dict],
    step_override: dict | None,
) -> dict | None:
    if step_override is not None:
        return step_override
    if session.state == "book" and activity:
        return flow.book_step(activity, lesson, session.quiz_index)[2]
    if session.state == "intro_chat":
        return intro_step(lesson, session.quiz_index)[2]
    if session.state == "self_check":
        can_dos = lesson.get("can_dos") or []
        if session.quiz_index < len(can_dos):
            return self_check_step(can_dos[session.quiz_index])
    if messages:
        for m in reversed(messages):
            if m.get("role") != "assistant":
                continue
            st = m.get("step") or {}
            if st.get("help"):
                continue
            return st
    return None


def _lesson_step_snapshot(
    session: ChatSession,
    lesson: dict,
    db: Session,
) -> dict:
    """Current exercise step — unchanged after a help reply."""
    activity = flow.track_by_id(lesson, session.activity_id)
    if session.state == "book" and activity:
        return dict(flow.book_step(activity, lesson, session.quiz_index)[2])
    if session.state == "intro_chat":
        return dict(intro_step(lesson, session.quiz_index)[2])
    if session.state == "self_check":
        can_dos = lesson.get("can_dos") or []
        if session.quiz_index < len(can_dos):
            return dict(self_check_step(can_dos[session.quiz_index]))
    if session.state == "can_do_quiz":
        can_dos = lesson.get("can_dos") or []
        if session.quiz_index < len(can_dos):
            cd = can_dos[session.quiz_index]
            scenario = _quiz_scenario(db, lesson, cd["id"])
            return dict(flow.quiz_step(cd, scenario, expect_speech=True))
    if session.state == "grammar":
        return {"phase": "grammar", "expect_speech": True, "play_audio": [], "help": False}
    if session.state == "lesson_intro":
        return {"phase": "intro", "expect_speech": False, "play_audio": [], "auto_advance_after_audio": True}
    return {"phase": session.state, "expect_speech": False, "play_audio": []}


def _payload(
    session: ChatSession,
    lesson: dict,
    messages: list[dict],
    step: dict | None = None,
    grade: dict | None = None,
    db: Session | None = None,
) -> dict:
    activity = flow.track_by_id(lesson, session.activity_id)
    last = messages[-1] if messages else {}
    resolved = _resolve_step(session, lesson, activity, messages, step)
    can_dos = lesson.get("can_dos") or []
    pending_self = None
    if session.state == "self_check" and session.quiz_index < len(can_dos):
        cd = can_dos[session.quiz_index]
        pending_self = {
            "can_do_id": cd.get("id"),
            "statement_en": cd.get("statement_en"),
            "statement_jp": cd.get("statement_jp"),
        }
    out = {
        "session_id": session.id,
        "lesson_id": lesson["lesson_id"],
        "state": session.state,
        "activity_id": session.activity_id,
        "activity": activity,
        "messages": messages,
        "can_dos": can_dos,
        "quiz_index": session.quiz_index,
        "step": resolved,
        "hint_en": last.get("hint_en"),
        "progress": lesson_progress_snapshot(lesson, session),
        "grade": grade,
        "self_check": pending_self,
        "next_lesson_id": next_lesson_id(lesson["lesson_id"])
        if session.state == "lesson_complete"
        else None,
    }
    if db is not None:
        out["self_checks"] = self_check_summary(db, lesson["lesson_id"], can_dos)
    return out


def _lesson_phrase_bank(lesson: dict) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for a in lesson.get("activities") or []:
        for p in a.get("key_phrases") or []:
            if p and p not in seen:
                seen.add(p)
                out.append(p)
    return out[:80]


async def ensure_session(db: Session, lesson_id: str) -> ChatSession:
    session = (
        db.query(ChatSession)
        .filter(ChatSession.lesson_id == lesson_id)
        .order_by(ChatSession.id.desc())
        .first()
    )
    if session:
        return session
    tracks = flow.book_tracks(load_lesson(lesson_id))
    first_id = tracks[0]["id"] if tracks else None
    session = ChatSession(
        lesson_id=lesson_id,
        state="lesson_intro",
        activity_id=first_id,
        quiz_index=0,
        messages_json="[]",
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def _can_do_passes(db: Session, can_do_id: str) -> int:
    row = db.get(CanDoProgress, can_do_id)
    return int(row.passes or 0) if row else 0


def _quiz_scenario(db: Session, lesson: dict, can_do_id: str) -> dict | None:
    return flow.pick_quiz_scenario(lesson, can_do_id, _can_do_passes(db, can_do_id))


def _prompt_can_do_quiz(
    db: Session,
    session: ChatSession,
    lesson: dict,
    messages: list[dict],
    can_do_index: int,
) -> dict:
    can_dos = lesson.get("can_dos") or []
    cd = can_dos[can_do_index]
    scenario = _quiz_scenario(db, lesson, cd["id"])
    jp, en, step = flow.quiz_prompt(cd, lesson, scenario)
    _append_tutor(messages, jp, en, step, session.state)
    return step


async def llm_refine_grade(
    user_text: str,
    can_do: dict,
    base: dict,
    scenario: dict | None = None,
) -> dict:
    prompt = [
        {
            "role": "system",
            "content": (
                "Grade A1 Japanese for Irodori can-do. Be lenient for beginners. "
                "Return JSON: {passed, score, gaps, jp_feedback}. "
                "jp_feedback must be very simple Japanese only, max 15 words, no English."
            ),
        },
        {
            "role": "user",
            "content": json.dumps(
                {
                    "can_do": can_do.get("statement_en"),
                    "must_include": (can_do.get("rubric") or {}).get("must_include"),
                    "partner_line": (scenario or {}).get("partner_jp"),
                    "acceptable_replies": (scenario or {}).get("expected"),
                    "learner": user_text,
                    "heuristic": base,
                },
                ensure_ascii=False,
            ),
        },
    ]
    try:
        raw = await ollama_client.chat(prompt, format_json=True)
        data = json.loads(raw)
        score = int(data.get("score", base["score"]))
        if base.get("gaps") and not base.get("hits") and (can_do.get("rubric") or {}).get("must_include") and not scenario:
            score = min(score, 50)
            data["passed"] = False
        data["score"] = score
        data["passed"] = bool(data.get("passed")) and score >= settings.mastery_min_score
        data["spoken"] = base.get("spoken", False)
        data["gaps"] = data.get("gaps") or base.get("gaps") or []
        data["jp_feedback"] = (data.get("jp_feedback") or "")[:80]
        return data
    except Exception:
        base["jp_feedback"] = flow.feedback_pass_short() if base.get("passed") else flow.feedback_retry(
            base.get("gaps") or []
        )
        return _apply_mastery_gate(base)


def apply_can_do_result(db: Session, lesson_id: str, can_do_id: str, grade: dict) -> CanDoProgress:
    row = db.get(CanDoProgress, can_do_id)
    if row is None:
        row = CanDoProgress(
            can_do_id=can_do_id,
            lesson_id=lesson_id,
            passes=0,
            spoken_passes=0,
            best_score=0.0,
            mastered=False,
        )
        db.add(row)
        db.flush()
    for attr, default in (("passes", 0), ("spoken_passes", 0), ("best_score", 0.0)):
        if getattr(row, attr) is None:
            setattr(row, attr, default)
    if grade.get("passed"):
        row.passes += 1
        if grade.get("spoken"):
            row.spoken_passes += 1
    row.best_score = max(float(row.best_score or 0), float(grade.get("score") or 0))
    row.mastered = (
        row.passes >= settings.mastery_passes_required
        and row.spoken_passes >= settings.mastery_spoken_required
    )
    row.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(row)
    return row


def check_lesson_mastery(db: Session, lesson_id: str) -> bool:
    lesson = load_lesson(lesson_id)
    for c in lesson.get("can_dos") or []:
        row = db.get(CanDoProgress, c["id"])
        if not row or not row.mastered:
            return False
    lp = db.get(LessonProgress, lesson_id) or LessonProgress(lesson_id=lesson_id, unlocked=True)
    if lp.lesson_id != lesson_id:
        db.add(lp)
    lp.mastered = True
    lp.updated_at = datetime.utcnow()
    nxt = next_lesson_id(lesson_id)
    if nxt:
        np = db.get(LessonProgress, nxt)
        if np is None:
            db.add(LessonProgress(lesson_id=nxt, unlocked=True))
        else:
            np.unlocked = True
    db.commit()
    log_event("orchestrator", "lesson_mastered", lesson_id=lesson_id, next_lesson=nxt)
    return True


def _begin_intro_chat(session: ChatSession, lesson: dict, messages: list[dict]) -> dict:
    """Warm-up questions before book tracks (skipped if YAML has none)."""
    qs = intro_questions(lesson)
    if not qs:
        tracks = flow.book_tracks(lesson)
        if tracks:
            session.activity_id = tracks[0]["id"]
        return _begin_book_track(session, lesson, messages)
    session.state = "intro_chat"
    session.quiz_index = 0
    jp, en, step = intro_step(lesson, 0)
    _append_tutor(messages, jp, en, step, session.state)
    return step


def _begin_book_track(session: ChatSession, lesson: dict, messages: list[dict]) -> dict:
    activity = flow.track_by_id(lesson, session.activity_id)
    if not activity:
        return _begin_grammar(session, lesson, messages)
    session.state = "book"
    session.quiz_index = 0
    intro = flow.book_section_intro(activity)
    if intro:
        jp_i, en_i = intro
        _append_tutor(
            messages,
            jp_i,
            en_i,
            {
                "phase": "book",
                "help": True,
                "expect_speech": False,
                "play_audio": [],
                "section_title_en": activity.get("book_section_en"),
            },
            session.state,
        )
    return _book_emit_step(session, lesson, activity, messages, 0)


def _after_can_do_passed(
    db: Session,
    session: ChatSession,
    lesson: dict,
    messages: list[dict],
    can_do: dict,
) -> dict:
    """Open soft self-check for this Can-do (does not unlock; quiz_index stays)."""
    session.state = "self_check"
    jp = "Can-do チェックです。じぶんの できを えらんでください。"
    en = "Soft self-check — how well could you do this? Stars only; unlock uses the graded quiz."
    step = self_check_step(can_do)
    _append_tutor(messages, jp, en, step, session.state)
    return step


def _continue_after_self_check(
    db: Session,
    session: ChatSession,
    lesson: dict,
    messages: list[dict],
) -> dict:
    """Move to next Can-do quiz or lesson complete after self-check."""
    can_dos = lesson.get("can_dos") or []
    session.quiz_index += 1
    if session.quiz_index >= len(can_dos):
        if check_lesson_mastery(db, lesson["lesson_id"]):
            session.state = "lesson_complete"
            jp, en = flow.lesson_complete_script()
            nxt = next_lesson_id(lesson["lesson_id"])
            step = {
                "phase": "complete",
                "expect_speech": False,
                "play_audio": [],
                "next_lesson_id": nxt,
            }
            _append_tutor(messages, jp, en, step, session.state)
            return step
        session.quiz_index = 0
        session.state = "can_do_quiz"
        return _prompt_can_do_quiz(db, session, lesson, messages, 0)
    session.state = "can_do_quiz"
    return _prompt_can_do_quiz(db, session, lesson, messages, session.quiz_index)


def _begin_grammar(session: ChatSession, lesson: dict, messages: list[dict]) -> dict:
    session.state = "grammar"
    session.activity_id = None
    session.quiz_index = 0
    pts = flow._grammar_for_lesson(lesson["lesson_id"])
    if not pts:
        jp, en, step = flow.grammar_intro(lesson["lesson_id"])
        _append_tutor(messages, jp, en, step, session.state)
        return step
    jp, en, step = flow.grammar_intro(lesson["lesson_id"])
    _append_tutor(messages, jp, en, step, session.state)
    jp2, en2, step2 = flow.grammar_item(pts[0], 0, len(pts))
    _append_tutor(messages, jp2, en2, step2, session.state)
    return step2


def _begin_quiz(session: ChatSession, lesson: dict, messages: list[dict], db: Session) -> dict:
    session.state = "can_do_quiz"
    session.activity_id = None
    session.quiz_index = 0
    can_dos = lesson.get("can_dos") or []
    if not can_dos:
        session.state = "lesson_complete"
        jp, en = flow.lesson_complete_script()
        step = {"phase": "complete", "expect_speech": False, "play_audio": []}
        _append_tutor(messages, jp, en, step, session.state)
        return step
    return _prompt_can_do_quiz(db, session, lesson, messages, 0)


def _next_book_track(session: ChatSession, lesson: dict) -> bool:
    tracks = flow.book_tracks(lesson)
    idx = flow.track_index(lesson, session.activity_id)
    if idx + 1 >= len(tracks):
        return False
    session.activity_id = tracks[idx + 1]["id"]
    session.quiz_index = 0
    return True


async def start_or_resume(db: Session, lesson_id: str) -> dict:
    if block := locked_response(db, lesson_id):
        return block
    lesson = load_lesson(lesson_id)
    session = await ensure_session(db, lesson_id)
    messages = _msgs(session)
    _sync_book_substep(session, messages)
    step = None
    if not messages:
        jp, en = flow.intro_script(lesson)
        step = {
            "phase": "intro",
            "play_audio": [],
            "expect_speech": False,
            "auto_advance_after_audio": True,
        }
        _append_tutor(messages, jp, en, step, "lesson_intro")
        session.state = "lesson_intro"
        _save_msgs(session, messages)
        db.commit()
        log_event("orchestrator", "start", lesson_id=lesson_id, new_session=True)
    else:
        log_event(
            "orchestrator",
            "resume",
            lesson_id=lesson_id,
            state=session.state,
            activity_id=session.activity_id,
            quiz_index=session.quiz_index,
            messages=len(messages),
        )
        db.commit()
    return _payload(session, lesson, messages, step)


async def advance(db: Session, lesson_id: str) -> dict:
    if block := locked_response(db, lesson_id):
        return block
    lesson = load_lesson(lesson_id)
    session = await ensure_session(db, lesson_id)
    messages = _msgs(session)
    step = None

    if session.state == "lesson_intro":
        step = _begin_intro_chat(session, lesson, messages)

    elif session.state == "intro_chat":
        # Skip remaining warm-up questions → book
        tracks = flow.book_tracks(lesson)
        if tracks:
            session.activity_id = tracks[0]["id"]
        step = _begin_book_track(session, lesson, messages)

    elif session.state == "book":
        activity = flow.track_by_id(lesson, session.activity_id)
        step = _book_advance_substep_or_track(session, lesson, messages, activity)

    elif session.state == "grammar":
        pts = flow._grammar_for_lesson(lesson_id)
        if not pts:
            step = _begin_quiz(session, lesson, messages, db)
        else:
            session.quiz_index += 1
            if session.quiz_index >= len(pts):
                step = _begin_quiz(session, lesson, messages, db)
            else:
                jp, en, step = flow.grammar_item(pts[session.quiz_index], session.quiz_index, len(pts))
                _append_tutor(messages, jp, en, step, session.state)

    elif session.state == "self_check":
        # Allow Skip on self-check without saving stars
        step = _continue_after_self_check(db, session, lesson, messages)

    elif session.state == "can_do_quiz":
        can_dos = lesson.get("can_dos") or []
        session.quiz_index += 1
        if session.quiz_index >= len(can_dos):
            if check_lesson_mastery(db, lesson_id):
                session.state = "lesson_complete"
                jp, en = flow.lesson_complete_script()
                nxt = next_lesson_id(lesson_id)
                step = {
                    "phase": "complete",
                    "expect_speech": False,
                    "play_audio": [],
                    "next_lesson_id": nxt,
                }
                _append_tutor(messages, jp, en, step, session.state)
            else:
                session.quiz_index = 0
                _announce_can_do_retry(db, session, lesson, messages)
                step = _prompt_can_do_quiz(db, session, lesson, messages, 0)
        else:
            step = _prompt_can_do_quiz(db, session, lesson, messages, session.quiz_index)

    _save_msgs(session, messages)
    db.commit()
    log_event(
        "orchestrator",
        "advance",
        lesson_id=lesson_id,
        state=session.state,
        activity_id=session.activity_id,
        quiz_index=session.quiz_index,
        step_phase=(step or {}).get("phase"),
        step_kind=(step or {}).get("kind"),
        book_substep=(step or {}).get("book_substep"),
    )
    return _payload(session, lesson, messages, step, db=db)


async def user_message(
    db: Session,
    lesson_id: str,
    text: str,
    *,
    spoken: bool = False,
) -> dict:
    if block := locked_response(db, lesson_id):
        return block
    lesson = load_lesson(lesson_id)
    session = await ensure_session(db, lesson_id)
    messages = _msgs(session)
    messages.append({"role": "user", "content": text, "spoken": spoken})
    activity = flow.track_by_id(lesson, session.activity_id)
    grade = None
    step = None
    log_event(
        "orchestrator",
        "user_message",
        lesson_id=lesson_id,
        state=session.state,
        activity_id=session.activity_id,
        activity_kind=(activity or {}).get("kind"),
        spoken=spoken,
        text=text[:200],
        quiz_index=session.quiz_index,
    )

    if session.state == "lesson_intro":
        step = _begin_intro_chat(session, lesson, messages)
        _save_msgs(session, messages)
        db.commit()
        return _payload(session, lesson, messages, step, db=db)

    if session.state == "intro_chat":
        # Free response — transcribe only, no grade
        jp_ack, en_ack = acknowledge_intro(text)
        qs = intro_questions(lesson)
        session.quiz_index += 1
        if session.quiz_index >= len(qs):
            _append_tutor(
                messages,
                jp_ack,
                en_ack,
                {"phase": "intro_chat", "expect_speech": False, "play_audio": []},
                session.state,
            )
            tracks = flow.book_tracks(lesson)
            if tracks:
                session.activity_id = tracks[0]["id"]
            step = _begin_book_track(session, lesson, messages)
        else:
            _append_tutor(
                messages,
                jp_ack,
                en_ack,
                {"phase": "intro_chat", "expect_speech": False, "play_audio": [], "help": True},
                session.state,
            )
            jp, en, step = intro_step(lesson, session.quiz_index)
            _append_tutor(messages, jp, en, step, session.state)
        _save_msgs(session, messages)
        db.commit()
        return _payload(session, lesson, messages, step, db=db)

    if session.state == "self_check":
        # Ignore free text during self-check; use dedicated endpoint
        can_dos = lesson.get("can_dos") or []
        cd = can_dos[session.quiz_index] if session.quiz_index < len(can_dos) else None
        step = self_check_step(cd) if cd else {"phase": "self_check", "expect_speech": False}
        _append_tutor(
            messages,
            "ほしを えらんでください。",
            "Please use the star rating (or Skip).",
            step,
            session.state,
        )
        _save_msgs(session, messages)
        db.commit()
        return _payload(session, lesson, messages, step, db=db)

    if session.state == "book" and activity:
        sub = substep_at(activity, session.quiz_index)
        if sub not in speech_substeps():
            jp = "この ステップは きく だけです。Skip か CDの あと つづけてください。"
            en = "This step is listen-only — wait for CD / tutor, or tap Skip."
            step = flow.book_step(activity, lesson, session.quiz_index)[2]
            _append_tutor(messages, jp, en, {**step, "expect_speech": False}, session.state)
            _save_msgs(session, messages)
            db.commit()
            return _payload(session, lesson, messages, step)

        must = flow.expected_phrases_for_substep(activity, session.quiz_index)
        grade = grade_phrases(text, must, spoken=spoken)
        log_event(
            "orchestrator",
            "grade",
            lesson_id=lesson_id,
            passed=grade.get("passed"),
            score=grade.get("score"),
            similarity=grade.get("similarity"),
            must=must,
            hits=grade.get("hits"),
            quiz_index=session.quiz_index,
            book_substep=sub,
        )
        if grade.get("passed"):
            reply = flow.feedback_pass_short()
            _append_tutor(
                messages,
                reply,
                grade.get("feedback_en") or "Good!",
                {"phase": "book", "expect_speech": False, "play_audio": []},
                session.state,
            )
            finishing_activity = session.quiz_index + 1 >= len(flow_substeps(activity))
            step = _book_advance_substep_or_track(session, lesson, messages, activity)
            if finishing_activity:
                srs_service.enqueue_vocab(
                    db, lesson["lesson_id"], flow._phrases(activity), activity.get("can_do_id")
                )
            _save_msgs(session, messages)
            db.commit()
            return _payload(session, lesson, messages, step, grade)
        reply = grade.get("feedback_jp") or flow.feedback_retry(must)
        step = flow.book_step(activity, lesson, session.quiz_index)[2]
        retry = dict(step)
        retry["play_audio"] = list(activity.get("audio") or [])[:1]
        retry["expect_speech"] = True
        _append_tutor(
            messages,
            reply,
            grade.get("feedback_en") or "Try again.",
            retry,
            session.state,
        )
        _save_msgs(session, messages)
        db.commit()
        return _payload(session, lesson, messages, retry, grade)

    if session.state == "grammar":
        reply = flow.feedback_pass_short() if len(text.strip()) >= 2 else flow.feedback_retry([])
        step = {"phase": "grammar", "expect_speech": True, "play_audio": []}
        _append_tutor(messages, reply, "Continue or tap Next.", step, session.state)
        _save_msgs(session, messages)
        db.commit()
        return _payload(session, lesson, messages, step)

    if session.state == "can_do_quiz":
        can_dos = lesson.get("can_dos") or []
        cd = can_dos[session.quiz_index] if session.quiz_index < len(can_dos) else None
        if cd:
            scenario = _quiz_scenario(db, lesson, cd["id"])
            must = (cd.get("rubric") or {}).get("must_include") or []
            expected = list((scenario or {}).get("expected") or must)
            mastery_th = float(settings.mastery_min_score)
            if scenario:
                base = quiz_grade(text, expected, spoken, pass_threshold=mastery_th)
            else:
                base = grade_phrases(text, must, spoken=spoken, pass_threshold=mastery_th)
            grade = await llm_refine_grade(text, cd, base, scenario)
            apply_can_do_result(db, lesson_id, cd["id"], grade)
            srs_service.enqueue_from_gaps(db, lesson_id, cd["id"], grade.get("gaps") or [], text)
            retry_phrases = expected if scenario else must
            if grade.get("passed"):
                reply = grade.get("jp_feedback") or flow.feedback_pass_short()
            else:
                reply = grade.get("jp_feedback") or flow.feedback_retry(retry_phrases)
            if grade.get("passed"):
                step = flow.quiz_step(cd, scenario, expect_speech=False)
            else:
                step = flow.quiz_step(cd, scenario, expect_speech=True)
            _append_tutor(
                messages,
                reply,
                f"Can-do score {grade.get('score')}%",
                step,
                session.state,
            )
            if grade.get("passed"):
                # Soft self-check before next Can-do / complete (unlock still from graded passes)
                step = _after_can_do_passed(db, session, lesson, messages, cd)
            _save_msgs(session, messages)
            db.commit()
            return _payload(session, lesson, messages, step, grade, db=db)
    reply = "つづけます。ボタンを おしてください。"
    _append_tutor(messages, reply, "Use Next activity to continue.", {"phase": "book", "expect_speech": False, "play_audio": []}, session.state)
    _save_msgs(session, messages)
    db.commit()
    return _payload(session, lesson, messages, None)


async def answer_question(
    db: Session,
    lesson_id: str,
    text: str,
    *,
    spoken: bool = False,
) -> dict:
    """Answer a learner question without advancing the lesson."""
    if block := locked_response(db, lesson_id):
        return block
    lesson = load_lesson(lesson_id)
    session = await ensure_session(db, lesson_id)
    messages = _msgs(session)
    activity = flow.track_by_id(lesson, session.activity_id)
    step_snapshot = _lesson_step_snapshot(session, lesson, db)
    # Ask Yuki must never advance lesson state — snapshot for restore after help reply.
    frozen = {
        "state": session.state,
        "activity_id": session.activity_id,
        "quiz_index": session.quiz_index,
    }

    messages.append({"role": "user", "content": text, "spoken": spoken, "kind": "question"})
    log_event(
        "orchestrator",
        "ask_question",
        lesson_id=lesson_id,
        state=session.state,
        activity_id=session.activity_id,
        text=text[:200],
    )

    jp, en = await _ollama_lesson_help(lesson, session, activity, step_snapshot, text)
    help_step = {**step_snapshot, "help": True}
    _append_tutor(messages, jp, en, help_step, session.state)
    # Restore session position (guard against accidental mutation in helpers).
    session.state = frozen["state"]
    session.activity_id = frozen["activity_id"]
    session.quiz_index = frozen["quiz_index"]
    _save_msgs(session, messages)
    db.commit()
    return _payload(session, lesson, messages, step_snapshot)


async def _ollama_lesson_help(
    lesson: dict,
    session: ChatSession,
    activity: dict | None,
    step: dict,
    question: str,
) -> tuple[str, str]:
    phrases = flow._phrases(activity) if activity else []
    grammar_pts = flow._grammar_for_lesson(lesson["lesson_id"])
    ctx = {
        "lesson_id": lesson["lesson_id"],
        "title_en": lesson.get("title_en"),
        "title_jp": lesson.get("title_jp"),
        "state": session.state,
        "lesson_phrases": _lesson_phrase_bank(lesson),
        "grammar_points": [g.get("point") for g in grammar_pts[:12]],
        "activity": {
            "book_activity": (activity or {}).get("book_activity"),
            "kind": (activity or {}).get("kind"),
            "book_mode": (activity or {}).get("book_mode"),
            "key_phrases": phrases,
            "phrase_meta": (activity or {}).get("phrase_meta"),
            "picture_hint_en": (activity or {}).get("picture_hint_en"),
        },
        "step": {
            "phase": step.get("phase"),
            "book_substep": step.get("book_substep"),
            "partner_jp": step.get("partner_jp"),
            "expected_phrases": step.get("expected_phrases"),
            "say_target_jp": step.get("say_target_jp"),
        },
    }
    prompt = [
        {
            "role": "system",
            "content": (
                "You are Yuki, a friendly A1 Japanese tutor (Irodori Starter). "
                "The learner paused mid-lesson to ask something. "
                "Return JSON only: {\"jp\": \"...\", \"en\": \"...\"}. "
                "jp: short, simple Japanese (1-3 sentences). "
                "en: clear English explanation. "
                "Use the lesson context and phrase list; if they ask what to say, give the phrase and meaning. "
                "Do not invent unrelated grammar. "
                "This is help only — do not tell them to skip ahead or finish the lesson."
            ),
        },
        {
            "role": "user",
            "content": json.dumps({"context": ctx, "question": question}, ensure_ascii=False),
        },
    ]
    try:
        raw = await ollama_client.chat(prompt, format_json=True)
        data = json.loads(raw)
        jp = (data.get("jp") or "").strip()[:500]
        en = (data.get("en") or "").strip()[:800]
        if jp and en:
            return jp, en
    except Exception as e:
        log_event("orchestrator", "ask_question_fallback", error=str(e)[:120])

    if phrases:
        jp = f"いってみてください。{phrases[0]}"
        en = f"For this step, try saying: {', '.join(phrases[:3])}"
    else:
        jp = "つづけましょう。わからない ときは もういちど きいてください。"
        en = "Let's continue. You can replay the book CD, or tap Skip if you're stuck."
    return jp, en


async def submit_self_check(
    db: Session,
    lesson_id: str,
    *,
    can_do_id: str,
    stars: int,
    comment: str = "",
) -> dict:
    """Store soft self-check and continue lesson flow. Does not affect unlock."""
    if block := locked_response(db, lesson_id):
        return block
    lesson = load_lesson(lesson_id)
    session = await ensure_session(db, lesson_id)
    messages = _msgs(session)
    if session.state != "self_check":
        return {"error": "Not waiting for a self-check.", "lesson_id": lesson_id}

    can_dos = lesson.get("can_dos") or []
    current = can_dos[session.quiz_index] if session.quiz_index < len(can_dos) else None
    if not current or current.get("id") != can_do_id:
        return {"error": "can_do_id does not match current self-check.", "lesson_id": lesson_id}

    save_self_check(db, lesson_id, can_do_id, stars, comment)
    log_event(
        "orchestrator",
        "self_check",
        lesson_id=lesson_id,
        can_do_id=can_do_id,
        stars=stars,
    )
    _append_tutor(
        messages,
        "記録しました。",
        f"Saved your self-check ({stars}★).",
        {"phase": "self_check", "expect_speech": False, "play_audio": [], "help": True},
        session.state,
    )
    step = _continue_after_self_check(db, session, lesson, messages)
    _save_msgs(session, messages)
    db.commit()
    return _payload(session, lesson, messages, step, db=db)


async def reset_lesson(db: Session, lesson_id: str) -> dict:
    if block := locked_response(db, lesson_id):
        return block
    log_event("orchestrator", "reset", lesson_id=lesson_id)
    db.query(ChatSession).filter(ChatSession.lesson_id == lesson_id).delete()
    db.commit()
    return await start_or_resume(db, lesson_id)


async def jump_to_can_do_quiz(db: Session, lesson_id: str, *, reset_can_do: bool = False) -> dict:
    """Skip book/grammar and open the first Can-do role-play (for testing)."""
    if block := locked_response(db, lesson_id):
        return block
    lesson = load_lesson(lesson_id)
    can_dos = lesson.get("can_dos") or []
    if not can_dos:
        return {"error": "This lesson has no Can-do checks.", "lesson_id": lesson_id}

    if reset_can_do:
        for c in can_dos:
            row = db.get(CanDoProgress, c["id"])
            if row:
                db.delete(row)
        db.commit()

    session = await ensure_session(db, lesson_id)
    messages = _msgs(session)
    session.state = "can_do_quiz"
    session.activity_id = None
    session.quiz_index = 0
    _append_tutor(
        messages,
        "Can-do テストに いきます。",
        "Jumped to Can-do quiz (book steps skipped).",
        {"phase": "quiz", "help": True, "expect_speech": False, "play_audio": []},
        session.state,
    )
    step = _prompt_can_do_quiz(db, session, lesson, messages, 0)
    _save_msgs(session, messages)
    db.commit()
    log_event(
        "orchestrator",
        "jump_can_do_quiz",
        lesson_id=lesson_id,
        reset_can_do=reset_can_do,
        can_do_id=can_dos[0].get("id"),
    )
    return _payload(session, lesson, messages, step)
