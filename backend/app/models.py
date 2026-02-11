import datetime as dt
import uuid

from sqlalchemy import JSON, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Study(Base):
    __tablename__ = "studies"

    id: Mapped[int] = mapped_column(primary_key=True)
    study_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255))
    retention_days: Mapped[int] = mapped_column(default=365)


class Participant(Base):
    __tablename__ = "participants"

    id: Mapped[int] = mapped_column(primary_key=True)
    participant_id: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    study_id: Mapped[str] = mapped_column(String(64), index=True)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=dt.datetime.utcnow)


class Session(Base):
    __tablename__ = "sessions"
    __table_args__ = (UniqueConstraint("session_id", name="uq_session_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[str] = mapped_column(String(128), index=True)
    participant_id: Mapped[str] = mapped_column(String(128), index=True)
    study_id: Mapped[str] = mapped_column(String(64), index=True)
    condition_id: Mapped[str] = mapped_column(String(64), index=True)
    start_time_utc: Mapped[dt.datetime] = mapped_column(DateTime)
    duration_sec: Mapped[float] = mapped_column(Float)
    completion_status: Mapped[str] = mapped_column(String(32))
    total_errors: Mapped[int] = mapped_column(Integer)
    hints_used: Mapped[int] = mapped_column(Integer)
    task_completion_time_sec: Mapped[float] = mapped_column(Float)
    score: Mapped[float | None] = mapped_column(Float, nullable=True)
    content_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    raw_artifact_path: Mapped[str] = mapped_column(Text)
    uploaded_at: Mapped[dt.datetime] = mapped_column(DateTime, default=dt.datetime.utcnow)

    events: Mapped[list["Event"]] = relationship(back_populates="session", cascade="all, delete-orphan")


class Event(Base):
    __tablename__ = "events"

    id: Mapped[int] = mapped_column(primary_key=True)
    event_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), unique=True, index=True, default=uuid.uuid4)
    session_id: Mapped[str] = mapped_column(ForeignKey("sessions.session_id", ondelete="CASCADE"), index=True)
    participant_id: Mapped[str] = mapped_column(String(128), index=True)
    study_id: Mapped[str] = mapped_column(String(64), index=True)
    condition_id: Mapped[str] = mapped_column(String(64), index=True)
    task_id: Mapped[str] = mapped_column(String(64), index=True)
    event_type: Mapped[str] = mapped_column(String(64), index=True)
    object_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    tool_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    hand: Mapped[str] = mapped_column(String(16), default="None")
    timestamp_utc: Mapped[dt.datetime] = mapped_column(DateTime)
    time_since_session_start_ms: Mapped[int] = mapped_column(Integer)
    position: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    rotation: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    extra: Mapped[dict] = mapped_column(JSON, default=dict)

    session: Mapped[Session] = relationship(back_populates="events")


class ComputedMetric(Base):
    __tablename__ = "computed_metrics"

    id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[str] = mapped_column(String(128), index=True)
    metric_name: Mapped[str] = mapped_column(String(128), index=True)
    metric_value: Mapped[float] = mapped_column(Float)
    dimension: Mapped[dict] = mapped_column(JSON, default=dict)
    computed_at: Mapped[dt.datetime] = mapped_column(DateTime, default=dt.datetime.utcnow)


class AnalysisRun(Base):
    __tablename__ = "analysis_runs"

    id: Mapped[int] = mapped_column(primary_key=True)
    run_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    study_id: Mapped[str] = mapped_column(String(64), index=True)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=dt.datetime.utcnow)
    exclusions_applied: Mapped[dict] = mapped_column(JSON, default=dict)
    tests_run: Mapped[dict] = mapped_column(JSON, default=dict)
    result_summary: Mapped[dict] = mapped_column(JSON, default=dict)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(32), default="viewer")
