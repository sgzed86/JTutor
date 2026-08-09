from __future__ import annotations

from backend.app import db as db_module

# Re-export for clarity
Base = db_module.Base
SessionLocal = db_module.SessionLocal
init_db = db_module.init_db
get_db = db_module.get_db
LessonProgress = db_module.LessonProgress
CanDoProgress = db_module.CanDoProgress
ChatSession = db_module.ChatSession
SrsCard = db_module.SrsCard
SrsReview = db_module.SrsReview
SettingRow = db_module.SettingRow
