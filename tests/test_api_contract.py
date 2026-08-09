"""HTTP contract: response envelope shape and the Ask-Yuki isolation guarantee."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from backend.app.main import app

REQUIRED_PAYLOAD_KEYS = {
    "kind",
    "session_id",
    "lesson_id",
    "state",
    "activity_id",
    "activity",
    "messages",
    "lesson_messages",
    "help_messages",
    "can_dos",
    "quiz_index",
    "step",
    "progress",
    "segments",
    "grammar",
    "vocab",
    "grade",
    "self_check",
    "self_checks",
    "next_lesson_id",
}


@pytest.fixture()
def client(clean_db):
    from backend.app.curriculum_loader import list_lessons
    from backend.app.db import LessonProgress, SessionLocal

    with SessionLocal() as db:
        for book in ("starter", "elementary1"):
            for entry in list_lessons(book):
                lid = str(entry["lesson_id"])
                row = db.get(LessonProgress, lid)
                if row is None:
                    db.add(LessonProgress(lesson_id=lid, unlocked=True))
                else:
                    row.unlocked = True
        db.commit()

    with TestClient(app) as c:
        yield c


def test_health_reports_services_and_identity(client):
    body = client.get("/health").json()
    assert body["ok"] is True
    assert body["app"] == "jtutor"
    assert body["instance_id"]
    assert set(body["services"]) == {"backend", "ollama", "voicevox", "whisper"}


def test_start_returns_the_full_envelope(client):
    body = client.post("/tutor/L01/start").json()
    missing = REQUIRED_PAYLOAD_KEYS - set(body)
    assert not missing, missing
    assert body["kind"] == "step"
    assert body["state"] == "lesson_intro"


def test_envelope_is_stable_across_endpoints(client):
    client.post("/tutor/L01/start")
    for call in (
        lambda: client.post("/tutor/L01/advance"),
        lambda: client.post("/tutor/L01/message", json={"text": "はい", "spoken": True}),
        lambda: client.post("/tutor/L01/ask", json={"text": "what do I say?"}),
    ):
        body = call().json()
        missing = REQUIRED_PAYLOAD_KEYS - set(body)
        assert not missing, missing


def test_unknown_lesson_returns_a_typed_error(client):
    r = client.post("/tutor/ZZ99/start")
    assert r.status_code == 404
    err = r.json()["error"]
    assert err["code"] == "lesson_not_found"
    assert err["message"] and err["hint"]
    assert err["retryable"] is False


def test_ask_never_moves_the_lesson(client, no_llm):
    client.post("/tutor/L02/start")
    before = client.post("/tutor/L02/advance").json()
    position = (before["state"], before["activity_id"], before["quiz_index"])

    after = client.post("/tutor/L02/ask", json={"text": "What does this mean?"}).json()

    assert (after["state"], after["activity_id"], after["quiz_index"]) == position
    # And the client must be able to tell that this is not a step transition.
    assert after["kind"] == "help"
    assert after["help_messages"], "the help reply should be on its own channel"


def test_ask_help_payload_is_not_actionable_as_a_transition(client, no_llm):
    """Regression: `/ask` echoes the current step, which for a `listen` sub-step
    carries play_audio + auto_advance. The client keyed off those and advanced
    the lesson. The payload now says `kind: "help"` so it can be ignored."""
    client.post("/tutor/L02/start")
    client.post("/tutor/L02/advance")
    step_payload = client.post("/tutor/L02/advance").json()
    assert step_payload["step"]["book_substep"] == "listen"
    assert step_payload["step"]["auto_advance"] is True

    help_payload = client.post("/tutor/L02/ask", json={"text": "help"}).json()
    assert help_payload["kind"] == "help"
    assert help_payload["state"] == step_payload["state"]
    assert help_payload["quiz_index"] == step_payload["quiz_index"]


def test_steps_are_self_describing(client):
    client.post("/tutor/L01/start")
    client.post("/tutor/L01/advance")  # intro -> warm-up
    body = client.post("/tutor/L01/advance").json()
    while body["state"] != "book":
        body = client.post("/tutor/L01/advance").json()
    step = body["step"]
    for key in ("substeps", "substep_index", "substep_total", "expects_speech", "auto_advance", "graded"):
        assert key in step, key
    assert step["substeps"], step
    assert isinstance(step.get("audio"), list)
    assert step.get("segment") is not None


def test_settings_round_trip(client):
    defaults = client.get("/settings").json()
    assert defaults["lessons"]["auto_advance"] == "after_audio"

    patched = client.patch(
        "/settings", json={"lessons": {"auto_advance": "off", "grading_strictness": "strict"}}
    ).json()
    assert patched["lessons"]["auto_advance"] == "off"
    assert patched["lessons"]["grading_strictness"] == "strict"
    assert client.get("/settings").json()["lessons"]["auto_advance"] == "off"

    reset = client.post("/settings/reset").json()
    assert reset["lessons"]["auto_advance"] == "after_audio"


def test_grading_strictness_is_honoured(client, no_llm):
    """A near-miss passes on lenient and fails on strict, through the API."""
    client.patch("/settings", json={"lessons": {"grading_strictness": "strict"}})
    from backend.app import user_settings
    from backend.app.phrase_grade import current_policy

    user_settings.invalidate_cache()
    assert current_policy().pass_threshold == 70.0

    client.patch("/settings", json={"lessons": {"grading_strictness": "lenient"}})
    user_settings.invalidate_cache()
    assert current_policy().pass_threshold == 48.0
    client.post("/settings/reset")
    user_settings.invalidate_cache()


def test_media_rejects_path_traversal(client):
    r = client.get("/media/audio", params={"path": "assets/audio/../../etc/passwd"})
    assert r.status_code == 400
    assert r.json()["error"]["code"] == "invalid_request"


def test_missing_audio_is_a_typed_error(client):
    r = client.get("/media/audio", params={"path": "assets/audio/does-not-exist.mp3"})
    assert r.status_code == 404
    assert r.json()["error"]["code"] == "audio_missing"
