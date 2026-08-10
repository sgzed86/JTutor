"""Activity → textbook page resolution via printed CD track codes."""

from __future__ import annotations

from backend.app.book_pages import resolve_activity_page, track_tags_from_activity


def test_track_tags_from_audio_path():
    assert track_tags_from_activity(
        {"audio": ["assets/audio/X_[04-02]_kotoba2.mp3"]}
    ) == ["04-02"]


def test_l04_vocab_stays_on_page_101():
    lesson = {"book_id": "starter", "pdf_pages": [101, 123]}
    a1 = {"id": "A1", "audio": ["assets/audio/X_[04-01]_kotoba1.mp3"], "key_phrases": ["ちち"]}
    a2 = {"id": "A2", "audio": ["assets/audio/X_[04-02]_kotoba2.mp3"], "key_phrases": ["あにです"]}
    assert resolve_activity_page(lesson, a1, [101, 123]) == 101
    assert resolve_activity_page(lesson, a2, [101, 123]) == 101


def test_l04_dialog_moves_to_page_102():
    lesson = {"book_id": "starter", "pdf_pages": [101, 123]}
    a3 = {"id": "A3", "audio": ["assets/audio/X_[04-03]_kiku1.mp3"]}
    assert resolve_activity_page(lesson, a3, [101, 123]) == 102


def test_explicit_pdf_page_override_wins():
    lesson = {"book_id": "starter", "pdf_pages": [101, 123]}
    activity = {"audio": ["assets/audio/X_[04-01]_kotoba1.mp3"], "pdf_page": 110}
    assert resolve_activity_page(lesson, activity, [101, 123]) == 110
