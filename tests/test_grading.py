"""Japanese phrase grading, pinned to current behaviour.

The normalization work (kanji/kana variants, katakana folding, n-gram blending,
soft passes for STT near-misses) is deliberate and must not drift.
"""

from __future__ import annotations

import pytest

from backend.app.phrase_grade import (
    DEFAULT_POLICY,
    GradingPolicy,
    diff_against,
    grade_phrases,
    normalize_jp_for_grade,
    quiz_grade,
    similarity_score,
)


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("おはよう", "おはよう"),
        ("お は よう。", "おはよう"),
        ("オハヨウ", "おはよう"),
        ("分かりません", "わかりません"),
        ("もう一度", "もういちど"),
        ("ありがとう御座います", "ありがとうございます"),
        ("すみません！", "すみません"),
        ("日本語", "にほんご"),
        ("コーヒー", "こーひー"),
    ],
)
def test_normalization(raw, expected):
    assert normalize_jp_for_grade(raw) == expected


@pytest.mark.parametrize(
    ("said", "target"),
    [
        ("おはよう", "おはよう"),
        ("オハヨウ", "おはよう"),
        ("あ、おはようございます", "おはようございます"),
        ("分かりました", "わかりました"),
        ("こんにちは。", "こんにちは"),
    ],
)
def test_clear_matches_pass(said, target):
    g = grade_phrases(said, [target], spoken=True)
    assert g["passed"] is True, g
    assert g["score"] >= DEFAULT_POLICY.pass_threshold


@pytest.mark.parametrize(
    ("said", "target"),
    [
        ("さようなら", "おはよう"),
        ("もう", "もういちどいってください"),
        ("", "おはよう"),
    ],
)
def test_clear_mismatches_fail(said, target):
    g = grade_phrases(said, [target], spoken=True)
    assert g["passed"] is False, g
    assert g["gaps"] == [target]


def test_multiple_candidates_take_the_best():
    g = grade_phrases("こんにちは", ["おはよう", "こんにちは", "こんばんは"], spoken=True)
    assert g["passed"] is True
    assert "こんにちは" in g["hits"]


def test_no_expected_phrases_accepts_any_japanese():
    assert grade_phrases("はい、そうです", [], spoken=True)["passed"] is True
    assert grade_phrases("hello", [], spoken=True)["passed"] is False


def test_strictness_changes_the_verdict_not_the_normalization():
    said, target = "こんにちは", "おはようございます"
    lenient = grade_phrases(said, [target], spoken=True, policy=GradingPolicy(48, 38))
    strict = grade_phrases(said, [target], spoken=True, policy=GradingPolicy(90, 80))
    assert strict["passed"] is False
    assert lenient["passed"] is False
    assert lenient["score"] == strict["score"]


def test_quiz_grade_floors_failing_scores():
    g = quiz_grade("ぜんぜんちがう", ["おはようございます"], True)
    assert g["passed"] is False
    assert g["score"] >= 40.0


def test_similarity_is_symmetricish_and_bounded():
    assert similarity_score("おはよう", "おはよう") == 100.0
    assert 0.0 <= similarity_score("あ", "おはようございます") <= 100.0


def test_diff_marks_missing_runs():
    runs = diff_against("おはよ", "おはようございます")
    assert runs, runs
    assert "".join(r["text"] for r in runs) == normalize_jp_for_grade("おはようございます")
    assert any(r["match"] for r in runs)
    assert any(not r["match"] for r in runs)


def test_ha_wa_feedback_for_mother():
    g = grade_phrases("わわ", ["はは"], spoken=True)
    assert g["passed"] is False
    assert "ha" in (g["feedback_en"] or "").lower()
    assert "wa" in (g["feedback_en"] or "").lower()


def test_mother_haha_still_passes():
    g = grade_phrases("はは", ["はは"], spoken=True)
    assert g["passed"] is True


def test_grade_reports_the_transcript_back():
    g = grade_phrases("おはよ", ["おはよう"], spoken=True)
    assert g["transcript"] == "おはよ"
