"""Book directions: kanji read-aloud, fill blanks match CD, grammar walks each line."""

from __future__ import annotations

from backend.app.book_modes import (
    flow_substeps,
    kanji_read_index,
    kanji_type_index,
    substep_at,
)
from backend.app.curriculum_loader import load_lesson
from backend.app.lesson_flow import (
    book_step,
    expected_for_blank,
    expected_phrases_for_substep,
    grammar_drills,
    grammar_item,
    track_by_id,
    _fill_prompt,
)


def _kanji_activity(lesson_id: str = "L03") -> dict:
    lesson = load_lesson(lesson_id)
    act = next(a for a in lesson["activities"] if a.get("book_mode") == "kanji_words")
    return act


def test_kanji_read_is_one_spoken_line_per_sentence():
    act = _kanji_activity("L03")
    sentences = act["kanji_sentences"]
    items = act["kanji_items"]
    subs = flow_substeps(act)
    assert subs[0] == "kanji_study"
    assert subs[1 : 1 + len(sentences)] == ["kanji_read"] * len(sentences)
    assert subs[1 + len(sentences) :] == ["kanji_type"] * len(items)

    lesson = load_lesson("L03")
    for i, line in enumerate(sentences):
        qi = 1 + i
        assert substep_at(act, qi) == "kanji_read"
        assert kanji_read_index(act, qi) == i
        jp, en, step = book_step(act, lesson, qi)
        assert step["expects_speech"] is True
        assert step["say_target_jp"] == line
        assert expected_phrases_for_substep(act, qi) == [line]
        assert "Read this line aloud" in en

    first_type = 1 + len(sentences)
    assert kanji_type_index(act, first_type) == 0
    assert substep_at(act, first_type) == "kanji_type"


def test_l04_a7_fill_blanks_match_cd_transcript():
    lesson = load_lesson("L04")
    act = track_by_id(lesson, "A7")
    assert act and act.get("book_mode") == "listen_fill"
    blanks = act["blanks"]
    assert len(blanks) == 3

    rebuilt = [_fill_prompt(b["prompt_jp"], b["answers"]) for b in blanks]
    assert rebuilt[0] == "呉さん、夫と子どもです。"
    assert rebuilt[1] == "バトさん、紹介します。"
    assert rebuilt[2] == "いもうととおとうとです。"
    for b, line in zip(blanks, rebuilt, strict=True):
        assert b["full_jp"] == line
        expected = expected_for_blank(b)
        assert line in expected
        assert b["answers"][0] in expected or any(a in expected for a in b["answers"])


def test_grammar_walks_each_example_line_when_no_exercises():
    drills = grammar_drills("L03")
    # L03 has curated examples and no facilitate exercises — one drill per example.
    assert len(drills) > 7  # more than one-per-point
    say_targets = []
    for i, d in enumerate(drills):
        assert d.get("facilitate") is False
        jp, en, step = grammar_item(d, i, len(drills))
        assert step["book_substep"] == "grammar_say"
        assert step["say_target_jp"]
        say_targets.append(step["say_target_jp"])
    # First point N です has three example lines.
    assert say_targets[:3] == ["トンです", "パクです", "私はマルシアです"]


def test_grammar_facilitate_still_walks_every_l04_turn():
    drills = grammar_drills("L04")
    kinds = [(d.get("turn") or {}).get("kind") for d in drills if d.get("facilitate")]
    assert kinds.count("listen") >= 15
    assert kinds.count("fill") == 14
    assert kinds.count("choose") == 5
    assert len(kinds) == len(drills)


def test_ocr_dialogue_grammar_points_are_skipped():
    drills = grammar_drills("EL01")
    points = [d.get("point") or "" for d in drills]
    assert not any(p.startswith("おはよう") for p in points)
    assert not any("→（" in p for p in points)
