from __future__ import annotations

from fastapi import APIRouter, Query
from pydantic import BaseModel, Field

from backend.app.config import settings
from backend.app.logging_setup import log_event, read_log_tail

router = APIRouter()


class ClientLogIn(BaseModel):
    source: str = "desktop"
    event: str
    detail: dict = Field(default_factory=dict)


@router.post("/client")
async def client_log(body: ClientLogIn):
    log_event(f"client.{body.source}", body.event, **body.detail)
    return {"ok": True}


@router.get("/tail")
def log_tail(lines: int = Query(200, ge=1, le=2000)):
    return {
        "path": str(settings.log_path),
        "lines": read_log_tail(lines),
    }
