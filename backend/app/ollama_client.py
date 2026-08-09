from __future__ import annotations

import httpx

from backend.app.config import settings


async def check_ollama() -> dict:
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            r = await client.get(f"{settings.ollama_url}/api/tags")
            r.raise_for_status()
            models = [m.get("name") for m in r.json().get("models", [])]
            return {"ok": True, "models": models, "selected": settings.ollama_model}
    except Exception as e:
        return {"ok": False, "error": str(e), "selected": settings.ollama_model}


async def chat(messages: list[dict], *, format_json: bool = False) -> str:
    payload: dict = {
        "model": settings.ollama_model,
        "messages": messages,
        "stream": False,
    }
    if format_json:
        payload["format"] = "json"
    async with httpx.AsyncClient(timeout=120.0) as client:
        r = await client.post(f"{settings.ollama_url}/api/chat", json=payload)
        r.raise_for_status()
        return r.json()["message"]["content"]
