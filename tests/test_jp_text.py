"""STT prompt helpers for short Japanese answers and numbers."""

from __future__ import annotations

from backend.app.speech.jp_text import (
    build_stt_prompt,
    cleanup_learner_transcript,
    digits_and_kanji_to_kana,
    int_to_kana,
    looks_numeric_or_short,
)


def test_int_to_kana_classroom_style():
    assert int_to_kana(0) == "ゼロ"
    assert int_to_kana(1) == "いち"
    assert int_to_kana(4) == "よん"
    assert int_to_kana(11) == "じゅういち"
    assert int_to_kana(25) == "にじゅうご"
    assert int_to_kana(95) == "きゅうじゅうご"


def test_digits_and_counters():
    assert digits_and_kanji_to_kana("25歳") == "にじゅうごさい"
    assert digits_and_kanji_to_kana("二十五歳です") == "にじゅうごさいです"


def test_short_and_numeric_hints():
    assert looks_numeric_or_short("いち")
    assert looks_numeric_or_short("25歳")
    assert looks_numeric_or_short("に")
    assert not looks_numeric_or_short("おはようございます、お元気ですか")


def test_stt_prompt_includes_number_bank_and_kana():
    prompt = build_stt_prompt("25歳です")
    assert prompt
    assert "にじゅうごさい" in prompt
    assert "いち" in prompt  # from number bank


def test_cleanup_drops_youtube_hallucinations():
    assert cleanup_learner_transcript("ご視聴ありがとうございました") == ""
    assert cleanup_learner_transcript("いち") == "いち"
