"""Tests for Japanese phrase grading."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backend.app.phrase_grade import expand_phrase_alternates, grade_phrases, similarity_score


def test_polite_casual_thanks():
    g = grade_phrases("ありがとう", ["ありがとうございます"], spoken=True)
    assert g["passed"], g


def test_negation_fails():
    g = grade_phrases("わかります", ["わかりません"], spoken=True)
    assert not g["passed"], g


def test_wrong_noun_fails():
    g = grade_phrases("肉が好きです", ["魚が好きです"], spoken=True)
    assert not g["passed"], g


def test_long_vowel_not_equal_short():
    assert similarity_score("ビール", "ビル") < 95


def test_honest_score_not_always_100():
    g = grade_phrases("おはよございます", ["おはようございます"], spoken=True, pass_threshold=58)
    if g["passed"]:
        assert g["score"] < 100 or g["similarity"] >= 99


def test_expand_equiv():
    alts = expand_phrase_alternates(["ありがとうございます"])
    assert "ありがとう" in alts
