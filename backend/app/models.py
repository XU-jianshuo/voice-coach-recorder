from datetime import datetime, timezone
from enum import StrEnum

from sqlalchemy import DateTime, Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class SessionStatus(StrEnum):
    queued = "queued"
    transcribing = "transcribing"
    transcribed = "transcribed"
    analyzing = "analyzing"
    analyzed = "analyzed"
    failed = "failed"


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class AudioSession(Base):
    __tablename__ = "audio_sessions"

    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    device_id: Mapped[str] = mapped_column(String(120), index=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    ended_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(40), default=SessionStatus.queued.value)
    audio_path: Mapped[str] = mapped_column(String(500))
    scene: Mapped[str | None] = mapped_column(String(120), nullable=True)
    privacy_level: Mapped[str | None] = mapped_column(String(80), nullable=True)
    session_metadata: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )

    transcript_segments: Mapped[list["TranscriptSegment"]] = relationship(
        back_populates="session", cascade="all, delete-orphan"
    )
    analysis: Mapped["CommunicationAnalysis | None"] = relationship(
        back_populates="session", cascade="all, delete-orphan"
    )


class TranscriptSegment(Base):
    __tablename__ = "transcript_segments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(ForeignKey("audio_sessions.id"), index=True)
    start_ms: Mapped[int] = mapped_column(Integer)
    end_ms: Mapped[int] = mapped_column(Integer)
    speaker_id: Mapped[str | None] = mapped_column(String(120), nullable=True)
    speaker_label: Mapped[str | None] = mapped_column(String(120), nullable=True)
    text: Mapped[str] = mapped_column(Text)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now
    )

    session: Mapped[AudioSession] = relationship(back_populates="transcript_segments")


class SpeakerProfile(Base):
    __tablename__ = "speaker_profiles"

    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    display_name: Mapped[str] = mapped_column(String(120))
    type: Mapped[str] = mapped_column(String(40))
    voiceprint_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now
    )


class CommunicationAnalysis(Base):
    __tablename__ = "communication_analyses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(
        ForeignKey("audio_sessions.id"), unique=True, index=True
    )
    summary: Mapped[str] = mapped_column(Text)
    scores: Mapped[dict] = mapped_column(JSON, default=dict)
    strengths: Mapped[list] = mapped_column(JSON, default=list)
    weaknesses: Mapped[list] = mapped_column(JSON, default=list)
    todos: Mapped[list] = mapped_column(JSON, default=list)
    better_phrases: Mapped[list] = mapped_column(JSON, default=list)
    raw_payload: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now
    )

    session: Mapped[AudioSession] = relationship(back_populates="analysis")


class Hotword(Base):
    __tablename__ = "hotwords"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    text: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    category: Mapped[str | None] = mapped_column(String(120), nullable=True)
    weight: Mapped[int] = mapped_column(Integer, default=10)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now
    )
