"""Can-do role-play grading prefers the local LLM judge."""

from __future__ import annotations

import asyncio
import json

from backend.app import lesson_flow as flow
from backend.app import orchestrator


def test_llm_judge_can_do_parses_pass(monkeypatch):
    async def fake_chat(messages, format_json=False, model=None):
        assert format_json
        return json.dumps(
            {
                "passed": True,
                "score": 90,
                "gaps": [],
                "jp_feedback": "よくできました。",
                "en_feedback": "You answered where you live clearly.",
            }
        )

    monkeypatch.setattr(orchestrator.ollama_client, "chat", fake_chat)
    grade = asyncio.run(
        orchestrator.llm_judge_can_do(
            "東京に住んでいます",
            {
                "statement_en": "Can ask and answer about where you live",
                "rubric": {"must_include": ["住んで"]},
            },
            {
                "partner_jp": "どこに住んでいますか？",
                "setup_en": "Answer where you live.",
                "goal_en": "Learner uses に住んでいます.",
                "expected": ["東京に住んでいます"],
            },
            spoken=True,
        )
    )
    assert grade is not None
    assert grade["passed"] is True
    assert grade["score"] == 90
    assert grade["judge"] == "llm"
    assert grade["spoken"] is True


def test_llm_judge_can_do_returns_none_when_ollama_down(monkeypatch):
    async def boom(*_a, **_k):
        raise RuntimeError("connection refused")

    monkeypatch.setattr(orchestrator.ollama_client, "chat", boom)
    grade = asyncio.run(orchestrator.llm_judge_can_do("はい", {"statement_en": "x"}, None))
    assert grade is None


def test_l04_quiz_scenarios_are_roleplays():
    from backend.app.curriculum_loader import load_lesson

    lesson = load_lesson("L04")
    scenarios = lesson.get("quiz_scenarios") or []
    assert scenarios
    assert all(s.get("setup_en") for s in scenarios)
    assert all(s.get("goal_en") for s in scenarios)
    picked = flow.pick_quiz_scenario(lesson, "CD_L04_13", 0)
    assert picked is not None
    assert "住んで" in (picked.get("partner_jp") or "") or "何歳" in (picked.get("partner_jp") or "")
    step = flow.quiz_step(
        next(c for c in lesson["can_dos"] if c["id"] == "CD_L04_13"),
        picked,
        expect_speech=True,
    )
    assert step["say_target_jp"] is None
    assert step["book_substep"] == "roleplay"


def test_all_lessons_have_curated_roleplays():
    from backend.app.curriculum_loader import load_lesson

    lesson_ids = [f"L{n:02d}" for n in range(1, 19)] + [f"EL{n:02d}" for n in range(1, 19)]
    for lid in lesson_ids:
        lesson = load_lesson(lid)
        scenarios = lesson.get("quiz_scenarios") or []
        can_dos = {c["id"] for c in (lesson.get("can_dos") or [])}
        assert scenarios, lid
        assert all(s.get("setup_en") and s.get("goal_en") for s in scenarios), lid
        covered = {s["can_do_id"] for s in scenarios}
        assert can_dos <= covered, f"{lid} missing scenarios for {can_dos - covered}"
        weak = {"では、お願いします。", "もう一度、お願いします。"}
        assert all((s.get("partner_jp") or "") not in weak for s in scenarios), lid


def test_enrich_turns_legacy_scenarios_into_roleplays():
    from backend.app.curriculum_loader import load_lesson

    lesson = load_lesson("L03")
    cd = next(c for c in lesson["can_dos"] if c["id"] == "CD_L03_07")
    raw = flow.pick_quiz_scenario(lesson, "CD_L03_07", 0)
    enriched = flow.enrich_quiz_scenario(cd, raw)
    assert enriched["setup_en"]
    assert enriched["goal_en"]
    step = flow.quiz_step(cd, raw, expect_speech=True)
    assert step["say_target_jp"] is None
    assert step["book_substep"] == "roleplay"
