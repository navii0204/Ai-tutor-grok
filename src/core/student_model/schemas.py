"""Pydantic v2 schemas for the student model — request/response contracts."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator


class ConceptMasterySchema(BaseModel):
    concept_id: str
    mastery_score: float = Field(ge=0.0, le=1.0)
    confidence: float = Field(ge=0.0, le=1.0)
    attempts: int = Field(ge=0)
    next_review_at: datetime | None = None
    last_interacted_at: datetime

    model_config = {"from_attributes": True}


class HolisticMarkersSchema(BaseModel):
    avg_reasoning_quality: float = Field(ge=0.0, le=1.0)
    learning_velocity: float
    concepts_mastered_count: int
    avg_reflection_depth: float = Field(ge=0.0, le=1.0)
    resilience_score: float = Field(ge=0.0, le=1.0)
    avg_focus_signal: float = Field(ge=0.0, le=1.0)
    ethical_moments_count: int
    values_alignment_score: float = Field(ge=0.0, le=1.0)
    total_sessions: int
    total_learning_minutes: int
    streak_days: int
    last_active_at: datetime | None = None

    model_config = {"from_attributes": True}


class StudentProfileSchema(BaseModel):
    id: str
    tenant_id: str
    external_id: str
    name: str
    grade: str
    segment: str
    language: str
    created_at: datetime
    holistic_markers: HolisticMarkersSchema | None = None
    concept_masteries: list[ConceptMasterySchema] = []

    model_config = {"from_attributes": True}


class CreateStudentRequest(BaseModel):
    external_id: str
    name: str
    grade: str
    segment: str = "school"
    language: str = "en"
    tenant_id: str | None = None


class UpdateMasteryRequest(BaseModel):
    concept_id: str
    delta_score: float = Field(description="Change in mastery score (can be negative)")
    reasoning_correct: bool = False
    session_id: str | None = None

    @field_validator("delta_score")
    @classmethod
    def validate_delta(cls, v: float) -> float:
        if abs(v) > 1.0:
            raise ValueError("delta_score must be between -1.0 and 1.0")
        return v


class SessionSummarySchema(BaseModel):
    session_type: str
    reasoning_quality: float
    reflection_depth: float
    focus_signal: float
    duration_seconds: int
    concept_ids: list[str]
    ethical_moments: list[dict[str, Any]] = []
    dialogue_summary: str | None = None
