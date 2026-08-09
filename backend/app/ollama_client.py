from __future__ import annotations

from collections.abc import AsyncIterator

import httpx

from backend.app.config import settings

# Connect fast (the engine is local: either it answers or it is not running),
# but allow a slow first token while a 7B model warms up.
_TIMEOUT = httpx.Timeout(connect=3.0, read=90.0, write=10.0, pool=5.0)


async def check_ollama() -> dict:
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            r = await client.get(f"{settings.ollama_url}/api/tags")
            r.raise_for_status()
            models = [m.get("name") for m in r.json().get("models", [])]
            return {"ok": True, "models": models, "selected": settings.ollama_model}
    except Exception as e:  # noqa: BLE001 - health probe reports, never raises
        return {"ok": False, "error": str(e), "selected": settings.ollama_model}


async def chat(
    messages: list[dict],
    *,
    format_json: bool = False,
    model: str | None = None,
) -> str:
    payload: dict = {
        "model": model or settings.ollama_model,
        "messages": messages,
        "stream": False,
    }
    if format_json:
        payload["format"] = "json"
    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        r = await client.post(f"{settings.ollama_url}/api/chat", json=payload)
        r.raise_for_status()
        return r.json()["message"]["content"]


async def chat_stream(
    messages: list[dict],
    *,
    model: str | None = None,
) -> AsyncIterator[str]:
    """Yield answer fragments as the model produces them."""
    import json

    payload = {
        "model": model or settings.ollama_model,
        "messages": messages,
        "stream": True,
    }
    async with (
        httpx.AsyncClient(timeout=_TIMEOUT) as client,
        client.stream("POST", f"{settings.ollama_url}/api/chat", json=payload) as r,
    ):
            r.raise_for_status()
            async for line in r.aiter_lines():
                if not line.strip():
                    continue
                try:
                    chunk = json.loads(line)
                except json.JSONDecodeError:
                    continue
                piece = (chunk.get("message") or {}).get("content")
                if piece:
                    yield piece
                if chunk.get("done"):
                    return
