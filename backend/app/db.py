from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    create_engine,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker

from backend.app.config import settings


class Base(DeclarativeBase):
    pass


class SettingRow(Base):
    __tablename__ = "settings"
    key: Mapped[str] = mapped_column(String(64), primary_key=True)
    value: Mapped[str] = mapped_column(Text, default="")


class LessonProgress(Base):
    __tablename__ = "lesson_progress"
    lesson_id: Mapped[str] = mapped_column(String(8), primary_key=True)
    unlocked: Mapped[bool] = mapped_column(Boolean, default=False)
    mastered: Mapped[bool] = mapped_column(Boolean, default=False)
    current_activity_id: Mapped[str | None] = mapped_column(String(16), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class CanDoProgress(Base):
    __tablename__ = "can_do_progress"
    can_do_id: Mapped[str] = mapped_column(String(32), primary_key=True)
    lesson_id: Mapped[str] = mapped_column(String(8), index=True)
    passes: Mapped[int] = mapped_column(Integer, default=0)
    spoken_passes: Mapped[int] = mapped_column(Integer, default=0)
    best_score: Mapped[float] = mapped_column(Float, default=0.0)
    mastered: Mapped[bool] = mapped_column(Boolean, default=False)
    # Soft self-check (stars) — does not affect unlock / mastery
    self_stars: Mapped[int | None] = mapped_column(Integer, nullable=True)
    self_comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class ChatSession(Base):
    __tablename__ = "chat_sessions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    lesson_id: Mapped[str] = mapped_column(String(8), index=True)
    state: Mapped[str] = mapped_column(String(32), default="lesson_intro")
    activity_id: Mapped[str | None] = mapped_column(String(16), nullable=True)
    quiz_index: Mapped[int] = mapped_column(Integer, default=0)
    messages_json: Mapped[str] = mapped_column(Text, default="[]")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class SrsCard(Base):
    __tablename__ = "srs_cards"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    card_type: Mapped[str] = mapped_column(String(32))
    lesson_id: Mapped[str] = mapped_column(String(8), index=True)
    can_do_id: Mapped[str | None] = mapped_column(String(32), nullable=True)
    front: Mapped[str] = mapped_column(Text)
    back: Mapped[str] = mapped_column(Text)
    audio_path: Mapped[str | None] = mapped_column(String(512), nullable=True)
    # FSRS state
    due: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    stability: Mapped[float] = mapped_column(Float, default=0.0)
    difficulty: Mapped[float] = mapped_column(Float, default=0.0)
    elapsed_days: Mapped[int] = mapped_column(Integer, default=0)
    scheduled_days: Mapped[int] = mapped_column(Integer, default=0)
    reps: Mapped[int] = mapped_column(Integer, default=0)
    lapses: Mapped[int] = mapped_column(Integer, default=0)
    state: Mapped[int] = mapped_column(Integer, default=0)  # 0=New
    last_review: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class SrsReview(Base):
    __tablename__ = "srs_reviews"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    card_id: Mapped[int] = mapped_column(Integer, ForeignKey("srs_cards.id"))
    rating: Mapped[int] = mapped_column(Integer)  # 1-4
    reviewed_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


engine = create_engine(f"sqlite:///{settings.db_path}", echo=False)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def _migrate_sqlite_columns() -> None:
    """Add new columns on existing SQLite DBs (create_all does not alter)."""
    from sqlalchemy import text

    with engine.begin() as conn:
        rows = conn.execute(text("PRAGMA table_info(can_do_progress)")).fetchall()
        names = {r[1] for r in rows}
        if "self_stars" not in names:
            conn.execute(text("ALTER TABLE can_do_progress ADD COLUMN self_stars INTEGER"))
        if "self_comment" not in names:
            conn.execute(text("ALTER TABLE can_do_progress ADD COLUMN self_comment TEXT"))


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
    try:
        _migrate_sqlite_columns()
    except Exception as exc:  # noqa: BLE001 - a failed migration must not block startup
        from backend.app.logging_setup import get_logger

        get_logger("db").warning("sqlite column migration failed: %s", exc)
    # Unlock first lesson(s) of each book by default
    with SessionLocal() as db:
        for lid, unlocked in [("L00", True), ("L01", True), ("EL01", True)]:
            row = db.get(LessonProgress, lid)
            if row is None:
                db.add(
                    LessonProgress(
                        lesson_id=lid,
                        unlocked=unlocked,
                        mastered=False,
                    )
                )
            elif lid in ("L01", "EL01") and not row.unlocked:
                row.unlocked = True
        if db.get(SettingRow, "active_book") is None:
            db.add(SettingRow(key="active_book", value="starter"))
        db.commit()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
