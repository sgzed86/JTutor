"""Unit coverage for the pieces the lesson flow is built from."""

from __future__ import annotations

import pytest

from backend.app import lesson_flow as flow
from backend.app.book_modes import (
    FLOW_BY_MODE,
    SUBSTEPS,
    auto_advance_substeps,
    flow_substeps,
    repeat_phrase_index,
    speech_substeps,
    substep_at,
)
from backend.app.curriculum_loader import load_lesson
from backend.app.free_response import intro_questions
from backend.app.lesson_unlock import next_lesson_id


def _activity(mode: str, phrases: list[str] | None = None) -> dict:
    return {"id": "A1", "book_mode": mode, "key_phrases": phrases or ["おはよう"]}


@pytest.mark.parametrize("mode", sorted(FLOW_BY_MODE))
def test_every_mode_yields_substeps(mode):
    subs = flow_substeps(_activity(mode))
    assert subs
    assert all(s in SUBSTEPS for s in subs)


def test_substep_sequences_are_unchanged():
    assert flow_substeps(_activity("listen_repeat")) == ["listen", "repeat"]
    assert flow_substeps(_activity("listen_select")) == ["listen", "select"]
    assert flow_substeps(_activity("shadow_dialog")) == ["shadow"]
    assert flow_substeps(_activity("dialog")) == [
        "listen",
        "shadow",
        "partner",
        "learner",
        "swap_learner",
        "swap_partner",
    ]


@pytest.mark.parametrize(
    ("phrases", "expected"),
    [([], 2), (["a"], 2), (["a", "b", "c"], 4)],
)
def test_listen_repeat_all_expands_per_phrase(phrases, expected):
    subs = flow_substeps(_activity("listen_repeat_all", phrases))
    assert len(subs) == expected
    assert subs[0] == "listen"
    assert set(subs[1:]) == {"repeat"}


def test_repeat_phrase_index_maps_quiz_index_to_phrase():
    a = _activity("listen_repeat_all", ["a", "b", "c"])
    assert repeat_phrase_index(a, 0) is None
    assert repeat_phrase_index(a, 1) == 0
    assert repeat_phrase_index(a, 3) == 2
    assert repeat_phrase_index(_activity("listen_repeat"), 1) is None


def test_substep_at_bounds():
    a = _activity("listen_repeat")
    assert substep_at(a, -5) == "listen"
    assert substep_at(a, 0) == "listen"
    assert substep_at(a, 1) == "repeat"
    assert substep_at(a, 2) is None


def test_derived_substep_sets_match_the_historical_hardcoded_ones():
    assert speech_substeps() == frozenset(name for name, spec in SUBSTEPS.items() if spec.expects_speech)
    assert auto_advance_substeps() == frozenset(name for name, spec in SUBSTEPS.items() if spec.auto_advances)


def test_next_lesson_id_across_books_and_ends():
    assert next_lesson_id("L01") == "L02"
    assert next_lesson_id("L18") is None
    assert next_lesson_id("EL01") == "EL02"
    assert next_lesson_id("EL18") is None
    assert next_lesson_id("nonsense") is None


def test_segments_group_consecutive_can_dos():
    lesson = load_lesson("L01")
    segments = flow.lesson_segments(lesson)
    assert segments
    assert all(s["total"] == len(segments) for s in segments)
    # Consecutive segments never repeat a can-do id back to back.
    ids = [s["can_do_id"] for s in segments]
    assert all(a != b for a, b in zip(ids, ids[1:], strict=False))
    # Every book activity belongs to exactly one segment.
    tracked = [a["id"] for a in flow.book_tracks(lesson)]
    covered = [aid for s in segments for aid in s["activity_ids"]]
    assert covered == tracked


def test_segment_lookup_for_activity():
    lesson = load_lesson("L01")
    first = flow.book_tracks(lesson)[0]["id"]
    seg = flow.segment_for_activity(lesson, first)
    assert seg and seg["index"] == 0 and seg["total"] >= 1
    assert flow.segment_for_activity(lesson, None) is None


def test_step_payload_is_self_describing():
    lesson = load_lesson("L01")
    activity = flow.book_tracks(lesson)[0]
    _jp, _en, step = flow.book_step(activity, lesson, 0)
    assert step["substeps"] == flow_substeps(activity)
    assert step["substep_index"] == 0
    assert step["expects_speech"] is False
    assert step["auto_advance"] is True
    assert step["expect_speech"] == step["expects_speech"]
    assert step["auto_advance_after_audio"] == step["auto_advance"]
    assert isinstance(step["audio"], list)


def test_audio_entries_attach_transcripts_when_available():
    lesson = load_lesson("L01")
    activity = flow.book_tracks(lesson)[0]
    _jp, _en, step = flow.book_step(activity, lesson, 0)
    for entry in step["audio"]:
        assert "path" in entry and "transcript" in entry


def test_intro_questions_normalizes_strings_and_dicts():
    assert intro_questions({"intro_questions": ["こんにちは"]}) == [
        {"jp": "こんにちは", "en": "こんにちは"}
    ]
    assert intro_questions({"intro_questions": [{"jp": "あ", "en": "b"}]}) == [{"jp": "あ", "en": "b"}]
    assert intro_questions({}) == []
    assert len(intro_questions({"intro_questions": ["a", "b", "c", "d", "e", "f"]})) == 4


def test_expected_phrases_for_repeat_accepts_alternates():
    activity = {
        "id": "A1",
        "book_mode": "listen_repeat",
        "key_phrases": ["おはよう", "おはようございます"],
    }
    got = flow.expected_phrases_for_substep(activity, 1)
    assert got[0] == "おはよう"
    assert "おはようございます" in got


def test_dialog_role_swap_keeps_book_colors_with_exchanged_lines():
    """Pass 1: Yuki yellow / student orange. Pass 2: student yellow / Yuki orange."""
    activity = {
        "id": "A16",
        "book_mode": "dialog",
        "key_phrases": ["ミロさんは何歳ですか", "25歳です"],
        "dialog_script": [
            {"speaker": "partner", "jp": "ミロさんは何歳ですか"},
            {"speaker": "learner", "jp": "25歳です"},
        ],
    }
    lesson = {"id": "L04", "title_en": "Age"}
    # listen=0, shadow=1, partner=2, learner=3, swap_learner=4, swap_partner=5
    jp_partner, _, partner = flow.book_step(activity, lesson, 2)
    assert partner["book_substep"] == "partner"
    assert partner["dialog_line_jp"] == "ミロさんは何歳ですか"
    assert partner["book_line_color"] == "yellow"
    assert partner["expect_speech"] is False
    assert jp_partner == "ミロさんは何歳ですか"

    jp_learner, _, learner = flow.book_step(activity, lesson, 3)
    assert learner["book_substep"] == "learner"
    assert learner["say_target_jp"] == "25歳です"
    assert learner["book_line_color"] == "orange"
    assert learner["expect_speech"] is True
    assert learner["model_before_speech"] is False
    assert learner.get("partner_jp") == "ミロさんは何歳ですか"
    assert jp_learner == ""  # no coach TTS — conversation reply

    jp_swap, _, swap_you = flow.book_step(activity, lesson, 4)
    assert swap_you["book_substep"] == "swap_learner"
    assert swap_you["say_target_jp"] == "ミロさんは何歳ですか"
    assert swap_you["book_line_color"] == "yellow"
    assert swap_you["expect_speech"] is True
    assert swap_you["model_before_speech"] is False
    assert "yellow" in (swap_you.get("instruction_en") or "").lower()
    assert "25歳" not in jp_swap  # must not model the learner line

    _, en, swap_yuki = flow.book_step(activity, lesson, 5)
    assert swap_yuki["book_substep"] == "swap_partner"
    assert swap_yuki["dialog_line_jp"] == "25歳です"
    assert swap_yuki["book_line_color"] == "orange"
    assert swap_yuki["expect_speech"] is False
    assert "orange" in (en or "").lower()

    assert flow.expected_phrases_for_substep(activity, 4)[0] == "ミロさんは何歳ですか"
