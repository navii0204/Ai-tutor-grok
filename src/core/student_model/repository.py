"""Data access layer for the student model.

Scalability note: Add Redis read-through caching per student_id to reduce
DB load. Cache invalidation happens on write in update_mastery / close_session.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.core.logging_config import get_logger
from .models import ConceptMastery, HolisticMarkers, SessionRecord, StudentProfile

log = get_logger(__name__)


class StudentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, student_id: str) -> StudentProfile | None:
        result = await self._session.execute(
            select(StudentProfile)
            .where(StudentProfile.id == student_id)
            .options(
                selectinload(StudentProfile.holistic_markers),
                selectinload(StudentProfile.concept_masteries),
            )
        )
        return result.scalar_one_or_none()

    async def get_by_external_id(self, tenant_id: str, external_id: str) -> StudentProfile | None:
        result = await self._session.execute(
            select(StudentProfile)
            .where(
                StudentProfile.tenant_id == tenant_id,
                StudentProfile.external_id == external_id,
            )
            .options(
                selectinload(StudentProfile.holistic_markers),
                selectinload(StudentProfile.concept_masteries),
            )
        )
        return result.scalar_one_or_none()

    async def create(
        self,
        tenant_id: str,
        external_id: str,
        name: str,
        grade: str,
        segment: str = "school",
        language: str = "en",
    ) -> StudentProfile:
        profile = StudentProfile(
            tenant_id=tenant_id,
            external_id=external_id,
            name=name,
            grade=grade,
            segment=segment,
            language=language,
        )
        markers = HolisticMarkers(tenant_id=tenant_id)
        profile.holistic_markers = markers
        self._session.add(profile)
        await self._session.flush()
        log.info("student_created", student_id=profile.id, tenant_id=tenant_id)
        return profile

    async def list_by_tenant(
        self, tenant_id: str, limit: int = 100, offset: int = 0
    ) -> list[StudentProfile]:
        result = await self._session.execute(
            select(StudentProfile)
            .where(StudentProfile.tenant_id == tenant_id)
            .limit(limit)
            .offset(offset)
            .options(
                selectinload(StudentProfile.holistic_markers),
                selectinload(StudentProfile.concept_masteries),
            )
        )
        return list(result.scalars().all())

    async def get_mastery(self, student_id: str, concept_id: str) -> ConceptMastery | None:
        result = await self._session.execute(
            select(ConceptMastery).where(
                ConceptMastery.student_id == student_id,
                ConceptMastery.concept_id == concept_id,
            )
        )
        return result.scalar_one_or_none()

    async def upsert_mastery(
        self,
        student_id: str,
        tenant_id: str,
        concept_id: str,
        mastery_score: float,
        confidence: float,
        reasoning_correct: bool,
        ease_factor: float,
        interval_days: int,
        next_review_at: datetime | None,
        segment: str = "school",
    ) -> ConceptMastery:
        existing = await self.get_mastery(student_id, concept_id)
        if existing:
            existing.mastery_score = max(0.0, min(1.0, mastery_score))
            existing.confidence = confidence
            existing.attempts += 1
            if reasoning_correct:
                existing.correct_reasoning_count += 1
            existing.ease_factor = ease_factor
            existing.interval_days = interval_days
            existing.next_review_at = next_review_at
            existing.last_interacted_at = datetime.now(timezone.utc)
            return existing
        cm = ConceptMastery(
            student_id=student_id,
            tenant_id=tenant_id,
            concept_id=concept_id,
            mastery_score=max(0.0, min(1.0, mastery_score)),
            confidence=confidence,
            attempts=1,
            correct_reasoning_count=1 if reasoning_correct else 0,
            ease_factor=ease_factor,
            interval_days=interval_days,
            next_review_at=next_review_at,
            segment=segment,
        )
        self._session.add(cm)
        await self._session.flush()
        return cm

    async def get_due_concepts(self, student_id: str, limit: int = 5) -> list[ConceptMastery]:
        now = datetime.now(timezone.utc)
        result = await self._session.execute(
            select(ConceptMastery)
            .where(
                ConceptMastery.student_id == student_id,
                ConceptMastery.next_review_at <= now,
            )
            .order_by(ConceptMastery.next_review_at)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def create_session(
        self,
        student_id: str,
        tenant_id: str,
        session_type: str,
        segment: str,
        concept_ids: list[str],
    ) -> SessionRecord:
        record = SessionRecord(
            student_id=student_id,
            tenant_id=tenant_id,
            session_type=session_type,
            segment=segment,
            concept_ids=concept_ids,
        )
        self._session.add(record)
        await self._session.flush()
        return record

    async def close_session(
        self,
        session_id: str,
        reasoning_quality: float,
        reflection_depth: float,
        focus_signal: float,
        duration_seconds: int,
        dialogue_summary: str | None,
        ethical_moments: list[dict[str, Any]],
    ) -> SessionRecord | None:
        result = await self._session.execute(
            select(SessionRecord).where(SessionRecord.id == session_id)
        )
        record = result.scalar_one_or_none()
        if record:
            record.ended_at = datetime.now(timezone.utc)
            record.reasoning_quality = reasoning_quality
            record.reflection_depth = reflection_depth
            record.focus_signal = focus_signal
            record.duration_seconds = duration_seconds
            record.dialogue_summary = dialogue_summary
            record.ethical_moments = ethical_moments
        return record

    async def update_holistic_markers(
        self, student_id: str, metrics: dict[str, Any]
    ) -> HolisticMarkers | None:
        result = await self._session.execute(
            select(HolisticMarkers).where(HolisticMarkers.student_id == student_id)
        )
        markers = result.scalar_one_or_none()
        if markers:
            for key, value in metrics.items():
                if hasattr(markers, key):
                    setattr(markers, key, value)
        return markers
