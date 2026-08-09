"""The per-run token guards the API without locking out the UI itself.

Regression: token-protecting `/` and `/assets/*` meant the packaged app's own
window loaded a JSON 401 instead of the interface — a top-level navigation
cannot attach a header.
"""

from __future__ import annotations

import importlib

import pytest
from fastapi.testclient import TestClient

TOKEN = "test-token-123"


@pytest.fixture()
def token_client(monkeypatch, clean_db):
    monkeypatch.setenv("JTUTOR_TOKEN", TOKEN)
    import backend.app.main as main_module

    importlib.reload(main_module)
    with TestClient(main_module.app) as client:
        yield client
    monkeypatch.delenv("JTUTOR_TOKEN", raising=False)
    importlib.reload(main_module)


def test_api_requires_the_token(token_client):
    r = token_client.post("/tutor/L01/start")
    assert r.status_code == 401
    assert r.json()["error"]["code"] == "unauthorized"


def test_api_accepts_the_token_header(token_client):
    r = token_client.post("/tutor/L01/start", headers={"x-jtutor-token": TOKEN})
    assert r.status_code == 200


def test_media_accepts_the_token_as_a_query_parameter(token_client):
    # <audio src> cannot set headers, so media URLs carry ?token=.
    r = token_client.get("/media/audio", params={"path": "assets/audio/nope.mp3", "token": TOKEN})
    assert r.status_code == 404
    assert r.json()["error"]["code"] == "audio_missing"


def test_health_stays_open_for_the_supervisor(token_client):
    assert token_client.get("/health").status_code == 200


def test_the_ui_document_is_not_token_protected(token_client):
    """The window loads `/` with no header; it must not get a 401 envelope."""
    r = token_client.get("/")
    assert r.status_code != 401
    body = r.json() if r.headers.get("content-type", "").startswith("application/json") else {}
    assert body.get("error", {}).get("code") != "unauthorized"


def test_ui_assets_are_not_token_protected(token_client):
    r = token_client.get("/assets/does-not-exist.js")
    assert r.status_code != 401
