"""User-adjustable application settings, persisted in the `settings` table.

Environment variables remain the *defaults*; anything the user changes in the
Settings panel is stored here so it survives restarts and is shared between the
Electron window and any browser tab.
"""

from __future__ import annotations

import json
from typing import Any, Literal

from pydantic import BaseModel, Field

from backend.app.config import settings as env_settings
from backend.app.logging_setup import get_logger

_log = get_logger("user_settings")
_KEY = "user_settings_v1"

Theme = Literal["system", "light", "dark"]
TextSize = Literal["normal", "large"]
JapaneseFont = Literal["mincho", "gothic"]
AutoAdvance = Literal["off", "after_audio", "after_audio_and_answer"]
Strictness = Literal["lenient", "standard", "strict"]
AskLanguage = Literal["en", "ja", "both"]
AskLength = Literal["brief", "normal", "detailed"]
MicMode = Literal["hold", "toggle"]

STRICTNESS_THRESHOLDS: dict[str, float] = {
    "lenient": 48.0,
    "standard": 58.0,
    "strict": 70.0,
}


class VoiceSettings(BaseModel):
    speaker_id: int | None = None
    speed: float = Field(default=1.0, ge=0.5, le=2.0)
    pitch: float = Field(default=0.0, ge=-0.15, le=0.15)
    fallback_to_system_voice: bool = True


class AudioSettings(BaseModel):
    input_device_id: str | None = None
    output_device_id: str | None = None
    tutor_volume: float = Field(default=1.0, ge=0.0, le=1.0)
    book_volume: float = Field(default=1.0, ge=0.0, le=1.0)
    book_rate: float = Field(default=1.0, ge=0.5, le=1.5)
    duck_tutor_under_book: bool = True


class AppearanceSettings(BaseModel):
    theme: Theme = "system"
    text_size: TextSize = "normal"
    japanese_font: JapaneseFont = "mincho"
    reduce_motion: bool = False


class LessonSettings(BaseModel):
    auto_advance: AutoAdvance = "after_audio"
    auto_advance_delay_ms: int = Field(default=1200, ge=0, le=3000)
    # After Yuki models the line, open the mic (toggle mode). Hold mode ignores this.
    auto_start_recording: bool = True
    # "toggle" = tap to speak, stop on silence or Stop. "hold" = press-and-hold fallback.
    mic_mode: MicMode = "toggle"
    auto_stop_on_silence: bool = True
    silence_ms: int = Field(default=1200, ge=400, le=4000)
    max_recording_ms: int = Field(default=15000, ge=3000, le=60000)
    confirm_before_send: bool = False
    grading_strictness: Strictness = "standard"
    show_romaji: bool = False
    show_furigana: bool = False


class AskYukiSettings(BaseModel):
    answer_language: AskLanguage = "both"
    speak_answer: bool = True
    answer_length: AskLength = "normal"
    model: str | None = None


class AdvancedSettings(BaseModel):
    whisper_model: str | None = None
    whisper_device: str | None = None
    developer_tools: bool = False


class UserSettings(BaseModel):
    # Missing from older saved JSON → treated as 0 so speech-UX migration runs.
    # Fresh defaults set this to CURRENT_PREFS_VERSION in `_defaults()`.
    prefs_version: int = 0
    voice: VoiceSettings = Field(default_factory=VoiceSettings)
    audio: AudioSettings = Field(default_factory=AudioSettings)
    appearance: AppearanceSettings = Field(default_factory=AppearanceSettings)
    lessons: LessonSettings = Field(default_factory=LessonSettings)
    ask_yuki: AskYukiSettings = Field(default_factory=AskYukiSettings)
    advanced: AdvancedSettings = Field(default_factory=AdvancedSettings)

    @property
    def pass_threshold(self) -> float:
        return STRICTNESS_THRESHOLDS[self.lessons.grading_strictness]


CURRENT_PREFS_VERSION = 3

_cache: UserSettings | None = None


def _defaults() -> UserSettings:
    s = UserSettings(prefs_version=CURRENT_PREFS_VERSION)
    strictness = (env_settings.grading_strictness or "standard").lower()
    if strictness in STRICTNESS_THRESHOLDS:
        s.lessons.grading_strictness = strictness  # type: ignore[assignment]
    s.ask_yuki.model = env_settings.ollama_model
    s.advanced.whisper_model = env_settings.whisper_model
    s.advanced.whisper_device = env_settings.whisper_device
    return s


def load() -> UserSettings:
    global _cache
    if _cache is not None:
        return _cache
    value = _defaults()
    try:
        from backend.app.db import SessionLocal, SettingRow

        with SessionLocal() as db:
            row = db.get(SettingRow, _KEY)
            if row and row.value:
                value = UserSettings.model_validate(json.loads(row.value))
    except Exception as exc:  # noqa: BLE001 - fall back to defaults, never fail startup
        _log.warning("could not load user settings: %s", exc)
    if value.prefs_version < CURRENT_PREFS_VERSION:
        # Prefer tap-to-speak + silence stop; hold remains available in Settings.
        value.lessons.mic_mode = "toggle"
        value.lessons.auto_stop_on_silence = True
        value.lessons.auto_start_recording = True
        value.prefs_version = CURRENT_PREFS_VERSION
        try:
            save(value)
        except Exception as exc:  # noqa: BLE001
            _log.warning("could not migrate speech prefs: %s", exc)
    _cache = value
    return value


def save(value: UserSettings) -> UserSettings:
    global _cache
    _cache = value
    try:
        from backend.app.db import SessionLocal, SettingRow

        payload = value.model_dump_json()
        with SessionLocal() as db:
            row = db.get(SettingRow, _KEY)
            if row is None:
                db.add(SettingRow(key=_KEY, value=payload))
            else:
                row.value = payload
            db.commit()
    except Exception as exc:  # noqa: BLE001 - in-process value still applies
        _log.warning("could not persist user settings: %s", exc)
    return value


def patch(changes: dict[str, Any]) -> UserSettings:
    """Deep-merge a partial update over the stored settings."""
    current = load().model_dump()
    for section, values in (changes or {}).items():
        if section not in current:
            continue
        if isinstance(values, dict) and isinstance(current[section], dict):
            current[section].update({k: v for k, v in values.items() if k in current[section]})
    return save(UserSettings.model_validate(current))


def reset() -> UserSettings:
    return save(_defaults())


def invalidate_cache() -> None:
    global _cache
    _cache = None
