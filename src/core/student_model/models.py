"""SQLAlchemy ORM models for the holistic student profile.

The student model is the nervous system of BrainEcosystem — every core engine
reads from and writes to it.  Design goals:
  - Micro-concept level mastery (not just chapter-level)
  - Holistic markers: cognitive + socio-emotional + mind-body signals
  - Time-series aware: spaced repetition intervals, velocity tracking
  - Multi-tenant: every row tagged with tenant_id for school isolation

Scalability note: At >100k students, partition ConceptMastery by tenant_id
or migrate to a time-series store (TimescaleDB) for velocity/SR data.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database import Base


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _uuid() -> str:
    return str(uuid.uuid4())


class StudentProfile(Base):
    """Top-level persistent student record (one per student per tenant)."""

    __tablename__ = "student_profiles"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    tenant_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    external_id: Mapped[str] = mapped_column(String(128), nullable=False)
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    grade: Mapped[str] = mapped_column(String(16), nullable=False)
    segment: Mapped[str] = mapped_column(String(32), nullable=False, default="school")
    language: Mapped[str] = mapped_column(String(16), nullable=False, default="en")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_now, onupdate=_now
    )

    # Relationships
    concept_masteries: Mapped[list[ConceptMastery]] = relationship(
        back_populates="student", cascade="all, delete-orphan", lazy="select"
    )
    sessions: Mapped[list[SessionRecord]] = relationship(
        back_populates="student", cascade="all, delete-orphan", lazy="select"
    )
    holistic_markers: Mapped[HolisticMarkers | None] = relationship(
        back_populates="student", cascade="all, delete-orphan", uselist=False, lazy="select"
    )

    __table_args__ = (
        UniqueConstraint("tenant_id", "external_id", name="uq_tenant_student"),
    )


class ConceptMastery(Base):
    """Micro-concept level mastery with spaced repetition metadata.

    Each row represents one student's mastery of one atomic concept.
    mastery_score: 0.0–1.0  (0 = unknown, 1 = fully mastered)
    confidence: 0.0–1.0     (model confidence in the mastery estimate)
    next_review_at: spaced-repetition scheduled review date
    """

    __tablename__ = "concept_masteries"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    student_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("student_profiles.id", ondelete="CASCADE"), index=True
    )
    tenant_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    concept_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    segment: Mapped[str] = mapped_column(String(32), nullable=False, default="school")

    mastery_score: Mapped[float] = mapped_column(Float, default=0.0)
    confidence: Mapped[float] = mapped_column(Float, default=0.5)
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    correct_reasoning_count: Mapped[int] = mapped_column(Integer, default=0)

    # Spaced repetition (SM-2 variant)
    ease_factor: Mapped[float] = mapped_column(Float, default=2.5)
    interval_days: Mapped[int] = mapped_column(Integer, default=1)
    next_review_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    last_interacted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_now
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    student: Mapped[StudentProfile] = relationship(back_populates="concept_masteries")

    __table_args__ = (
        UniqueConstraint("student_id", "concept_id", name="uq_student_concept"),
    )


class SessionRecord(Base):
    """Persists one learning session (chat/simulator/assessment).

    dialogue_summary: LLM-generated summary of key reasoning steps in the session.
    reasoning_quality: 0.0–1.0 holistic score for the session's reasoning.
    reflection_depth: 0.0–1.0 measure of how deeply the student reflected.
    focus_signal: 0.0–1.0 engagement/focus indicator for the session.
    """

    __tablename__ = "session_records"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    student_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("student_profiles.id", ondelete="CASCADE"), index=True
    )
    tenant_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    session_type: Mapped[str] = mapped_column(
        String(32), nullable=False, default="chat"
    )  # chat | simulator | assessment | reflection
    segment: Mapped[str] = mapped_column(String(32), nullable=False, default="school")
    concept_ids: Mapped[list[str]] = mapped_column(JSON, default=list)

    dialogue_summary: Mapped[str | None] = mapped_column(Text)
    reasoning_quality: Mapped[float] = mapped_column(Float, default=0.0)
    reflection_depth: Mapped[float] = mapped_column(Float, default=0.0)
    focus_signal: Mapped[float] = mapped_column(Float, default=0.5)
    ethical_moments: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)

    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    duration_seconds: Mapped[int] = mapped_column(Integer, default=0)

    raw_metrics: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)

    student: Mapped[StudentProfile] = relationship(back_populates="sessions")


class HolisticMarkers(Base):
    """Persistent holistic growth markers for a student (one row per student).

    Cognitive: average reasoning quality across sessions.
    Emotional: self-regulation, reflection depth, resilience in struggle.
    Mind-body: focus signals, reflection practice frequency.
    Ethical: count of ethical reasoning moments, values alignment score.

    Scalability note: These can be materialised as a cached read-model
    computed asynchronously by the analytics engine after each session.
    """

    __tablename__ = "holistic_markers"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    student_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("student_profiles.id", ondelete="CASCADE"),
        unique=True,
        index=True,
    )
    tenant_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)

    # Cognitive
    avg_reasoning_quality: Mapped[float] = mapped_column(Float, default=0.0)
    learning_velocity: Mapped[float] = mapped_column(Float, default=0.0)
    concepts_mastered_count: Mapped[int] = mapped_column(Integer, default=0)

    # Emotional / Socio-emotional
    avg_reflection_depth: Mapped[float] = mapped_column(Float, default=0.0)
    resilience_score: Mapped[float] = mapped_column(Float, default=0.5)
    persistence_index: Mapped[float] = mapped_column(Float, default=0.5)

    # Mind-body alignment
    avg_focus_signal: Mapped[float] = mapped_column(Float, default=0.5)
    reflection_practice_count: Mapped[int] = mapped_column(Integer, default=0)

    # Ethical / Values
    ethical_moments_count: Mapped[int] = mapped_column(Integer, default=0)
    values_alignment_score: Mapped[float] = mapped_column(Float, default=0.5)

    total_sessions: Mapped[int] = mapped_column(Integer, default=0)
    total_learning_minutes: Mapped[int] = mapped_column(Integer, default=0)
    streak_days: Mapped[int] = mapped_column(Integer, default=0)
    last_active_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_now, onupdate=_now
    )

    student: Mapped[StudentProfile] = relationship(back_populates="holistic_markers")
