from __future__ import annotations

import os
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


def _default_root() -> Path:
    env = os.environ.get("JTUTOR_ROOT", "").strip()
    if env:
        return Path(env).expanduser().resolve()
    return Path(__file__).resolve().parents[2]


def _env_path(name: str) -> Path | None:
    raw = os.environ.get(name, "").strip()
    return Path(raw).expanduser().resolve() if raw else None


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    root_dir: Path = _default_root()
    # Writable state (SQLite, logs, TTS cache). Defaults to <root>/data, but the
    # Electron supervisor points this at the per-user app data folder so an
    # install under Program Files still works.
    data_dir_override: Path | None = _env_path("JTUTOR_DATA_DIR")
    assets_dir_override: Path | None = _env_path("JTUTOR_ASSETS_DIR")
    host: str = "127.0.0.1"
    # 0 means "let the supervisor choose"; the dev server still defaults to 8765.
    port: int = 8765
    ollama_url: str = "http://127.0.0.1:11434"
    ollama_model: str = "qwen2.5:7b"
    voicevox_url: str = "http://127.0.0.1:50021"
    # Runtime-selected VoiceVox style id (overridable via POST /voice/set-speaker).
    selected_speaker_id: int = 2
    # Legacy env alias — used only if SELECTED_SPEAKER_ID is unset and this is set.
    voicevox_speaker: int = 2
    whisper_model: str = "small"
    whisper_device: str = "cpu"
    mastery_min_score: int = 80
    # lenient | standard | strict — maps to the phrase-grading pass threshold.
    # Can-do mastery thresholds are deliberately NOT affected by this.
    grading_strictness: str = "standard"
    mastery_passes_required: int = 1
    mastery_spoken_required: int = 1
    srs_daily_review_cap: int = 20
    srs_daily_new_cap: int = 10
    voice_speed_scale: float = 0.95
    tutor_message_window: int = 80
    log_level: str = "INFO"
    # Active book id: starter | elementary1 (overridable via settings DB / API)
    active_book: str = "starter"

    @property
    def log_path(self) -> Path:
        return self.data_dir / "jtutor.log"

    @property
    def content_dir(self) -> Path:
        from backend.app.books import content_dir_for_book

        return content_dir_for_book(self.active_book)

    @property
    def assets_dir(self) -> Path:
        return self.assets_dir_override or (self.root_dir / "assets")

    @property
    def data_dir(self) -> Path:
        d = self.data_dir_override or (self.root_dir / "data")
        d.mkdir(parents=True, exist_ok=True)
        return d

    @property
    def tts_cache_dir(self) -> Path:
        d = self.data_dir / "tts-cache"
        d.mkdir(parents=True, exist_ok=True)
        return d

    @property
    def db_path(self) -> Path:
        return self.data_dir / "jtutor.db"


settings = Settings()
