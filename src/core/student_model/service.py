"""StudentModelService — business logic between API and repository.

Owns mastery updates with SM-2 spaced repetition, holistic marker aggregation,
and learning velocity computation.
"""

from __future__ import annotations

import math
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.logging_config import get_logger
from .models import ConceptMastery, SessionRecord, StudentProfile
from .repository import StudentRepository
from .schemas import (
    CreateStudentRequest,
    SessionSummarySchema,
    UpdateMasteryRequest,
)

log = get_logger(__name__)


class StudentModelService:
    """Facade for all student model operations.

    Inject via FastAPI dependency to keep business logic out of route handlers.
    """

    def __init__(self, session: AsyncSession, default_tenant_id: str) -> None:
        self._repo = StudentRepository(session)
        self._default_tenant = default_tenant_id

    async def get_or_create_student(self, req: CreateStudentRequest) -> StudentProfile:
        tenant_id = req.tenant_id or self._default_tenant
        profile = await self._repo.get_by_external_id(tenant_id, req.external_id)
        if not profile:
            profile = await self._repo.create(
                tenant_id=tenant_id,
                external_id=req.external_id,
                name=req.name,
                grade=req.grade,
                segment=req.segment,
                language=req.language,
            )
        return profile

    async def get_student(self, student_id: str) -> StudentProfile | None:
        return await self._repo.get_by_id(student_id)

    async def update_concept_mastery(
        self,
        student_id: str,
        tenant_id: str,
        req: UpdateMasteryRequest,
        segment: str = "school",
    ) -> ConceptMastery:
        existing = await self._repo.get_mastery(student_id, req.concept_id)

        current_score = existing.mastery_score if existing else 0.0
        current_ef = existing.ease_factor if existing else 2.5
        current_interval = existing.interval_days if existing else 1

        new_score = max(0.0, min(1.0, current_score + req.delta_score))
        quality = self._score_to_sr_quality(req.delta_score, req.reasoning_correct)
        new_ef, new_interval, next_review = self._sm2(quality, current_ef, current_interval)
        confidence = self._estimate_confidence(
            existing.attempts if existing else 0, new_score
        )

        mastery = await self._repo.upsert_mastery(
            student_id=student_id,
            tenant_id=tenant_id,
            concept_id=req.concept_id,
            mastery_score=new_score,
            confidence=confidence,
            reasoning_correct=req.reasoning_correct,
            ease_factor=new_ef,
            interval_days=new_interval,
            next_review_at=next_review,
            segment=segment,
        )
        log.info(
            "mastery_updated",
            student_id=student_id,
            concept_id=req.concept_id,
            score=new_score,
        )
        return mastery

    async def open_session(
        self,
        student_id: str,
        tenant_id: str,
        session_type: str,
        segment: str,
        concept_ids: list[str],
    ) -> SessionRecord:
        return await self._repo.create_session(
            student_id=student_id,
            tenant_id=tenant_id,
            session_type=session_type,
            segment=segment,
            concept_ids=concept_ids,
        )

    async def close_session(
        self, session_id: str, student_id: str, summary: SessionSummarySchema
    ) -> SessionRecord | None:
        record = await self._repo.close_session(
            session_id=session_id,
            reasoning_quality=summary.reasoning_quality,
            reflection_depth=summary.reflection_depth,
            focus_signal=summary.focus_signal,
            duration_seconds=summary.duration_seconds,
            dialogue_summary=summary.dialogue_summary,
            ethical_moments=summary.ethical_moments,
        )
        await self._aggregate_holistic_markers(student_id, summary)
        return record

    async def get_due_review_concepts(self, student_id: str) -> list[ConceptMastery]:
        return await self._repo.get_due_concepts(student_id)

    async def list_students(
        self, tenant_id: str, limit: int = 100, offset: int = 0
    ) -> list[StudentProfile]:
        return await self._repo.list_by_tenant(tenant_id, limit, offset)

    # ── SM-2 spaced repetition ─────────────────────────────────────────────────

    def _sm2(
        self, quality: int, ef: float, interval: int
    ) -> tuple[float, int, datetime | None]:
        if quality < 3:
            new_interval = 1
            new_ef = ef
        else:
            new_interval = 1 if interval <= 1 else (6 if interval == 6 else round(interval * ef))
            new_ef = max(1.3, ef + 0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
        next_review = datetime.now(timezone.utc) + timedelta(days=new_interval)
        return new_ef, new_interval, next_review

    def _score_to_sr_quality(self, delta: float, reasoning_correct: bool) -> int:
        if reasoning_correct and delta >= 0.2:
            return 5
        if reasoning_correct and delta >= 0.1:
            return 4
        if delta >= 0.05:
            return 3
        if delta >= 0:
            return 2
        return 1

    def _estimate_confidence(self, attempts: int, score: float) -> float:
        base = 1 - math.exp(-0.3 * attempts)
        return round(base * (0.5 + 0.5 * score), 3)

    async def _aggregate_holistic_markers(
        self, student_id: str, summary: SessionSummarySchema
    ) -> None:
        """Incrementally update holistic markers after a session closes.

        Scalability note: Move this to an ARQ/Celery background task for
        high throughput — fire-and-forget after session close.
        """
        profile = await self._repo.get_by_id(student_id)
        if not profile or not profile.holistic_markers:
            return
        m = profile.holistic_markers

        def ema(old: float, new: float, alpha: float = 0.3) -> float:
            return alpha * new + (1 - alpha) * old

        updates: dict[str, Any] = {
            "total_sessions": m.total_sessions + 1,
            "total_learning_minutes": m.total_learning_minutes + summary.duration_seconds // 60,
            "avg_reasoning_quality": ema(m.avg_reasoning_quality, summary.reasoning_quality),
            "avg_reflection_depth": ema(m.avg_reflection_depth, summary.reflection_depth),
            "avg_focus_signal": ema(m.avg_focus_signal, summary.focus_signal),
            "ethical_moments_count": m.ethical_moments_count + len(summary.ethical_moments),
            "last_active_at": datetime.now(timezone.utc),
        }
        await self._repo.update_holistic_markers(student_id, updates)
