"""Machine-readable error envelope.

Every failure the UI has to explain carries a stable `code`, a learner-facing
`message`, an actionable `hint` and a `retryable` flag, so the client can pick
between a quiet chip, an inline notice and a blocking dialog without parsing
prose.
"""

from __future__ import annotations

from typing import Any

from fastapi import Request
from fastapi.responses import JSONResponse


class JtutorError(Exception):
    status_code = 500
    code = "internal_error"
    message = "Something went wrong."
    hint: str | None = None
    retryable = False

    def __init__(
        self,
        message: str | None = None,
        *,
        hint: str | None = None,
        detail: str | None = None,
        retryable: bool | None = None,
    ) -> None:
        super().__init__(message or self.message)
        if message:
            self.message = message
        if hint is not None:
            self.hint = hint
        if retryable is not None:
            self.retryable = retryable
        self.detail = detail

    def envelope(self) -> dict[str, Any]:
        return {
            "error": {
                "code": self.code,
                "message": self.message,
                "hint": self.hint,
                "retryable": self.retryable,
                "detail": self.detail,
            }
        }


class LessonNotFound(JtutorError):
    status_code = 404
    code = "lesson_not_found"
    message = "That lesson isn't in the current book."
    hint = "Switch books, or rebuild the curriculum."


class LessonLocked(JtutorError):
    status_code = 403
    code = "lesson_locked"
    message = "This lesson is still locked."
    hint = "Finish the Can-do checks in the previous lesson first."


class VoicevoxDown(JtutorError):
    status_code = 503
    code = "voicevox_unavailable"
    message = "VOICEVOX isn't running, so Yuki has no voice."
    hint = "Start VOICEVOX, or switch to the system voice in Settings."
    retryable = True


class WhisperDown(JtutorError):
    status_code = 503
    code = "whisper_unavailable"
    message = "Speech recognition isn't available."
    hint = "Check Settings → Advanced for the speech model status."
    retryable = True


class OllamaDown(JtutorError):
    status_code = 503
    code = "ollama_unavailable"
    message = "Yuki can't reach the language model."
    hint = "Start Ollama, or keep going — you'll still get phrase hints."
    retryable = True


class AudioNotFound(JtutorError):
    status_code = 404
    code = "audio_missing"
    message = "That book track isn't in your audio folder."
    hint = "Add the Irodori MP3s to your assets folder, or continue without audio."


class PdfNotFound(JtutorError):
    status_code = 404
    code = "pdf_missing"
    message = "That PDF isn't in your assets folder."
    hint = "Add the Irodori PDFs to your assets folder."


class InvalidRequest(JtutorError):
    status_code = 400
    code = "invalid_request"
    message = "That request wasn't valid."


class Unauthorized(JtutorError):
    status_code = 401
    code = "unauthorized"
    message = "This request is missing the app token."
    hint = "Restart Jtutor."


async def jtutor_error_handler(_request: Request, exc: JtutorError) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content=exc.envelope())
