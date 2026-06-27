"""Tests for the student model service and SM-2 spaced repetition."""

from __future__ import annotations

import pytest

from src.core.student_model.schemas import CreateStudentRequest, UpdateMasteryRequest
from src.core.student_model.service import StudentModelService


@pytest.mark.asyncio
async def test_create_student(student_service: StudentModelService):
    req = CreateStudentRequest(
        external_id="stu001",
        name="Arjun Sharma",
        grade="7",
        segment="school",
        tenant_id="test-tenant",
    )
    student = await student_service.get_or_create_student(req)
    assert student.id
    assert student.name == "Arjun Sharma"
    assert student.grade == "7"
    assert student.holistic_markers is not None


@pytest.mark.asyncio
async def test_idempotent_student_creation(student_service: StudentModelService):
    """Creating the same student twice returns the same record."""
    req = CreateStudentRequest(
        external_id="stu002",
        name="Priya Nair",
        grade="8",
        segment="school",
        tenant_id="test-tenant",
    )
    s1 = await student_service.get_or_create_student(req)
    s2 = await student_service.get_or_create_student(req)
    assert s1.id == s2.id


@pytest.mark.asyncio
async def test_update_mastery(student_service: StudentModelService):
    req = CreateStudentRequest(
        external_id="stu003",
        name="Rahul Gupta",
        grade="6",
        segment="school",
        tenant_id="test-tenant",
    )
    student = await student_service.get_or_create_student(req)

    mastery = await student_service.update_concept_mastery(
        student_id=student.id,
        tenant_id="test-tenant",
        req=UpdateMasteryRequest(
            concept_id="math_fractions_basic",
            delta_score=0.2,
            reasoning_correct=True,
        ),
    )
    assert mastery.mastery_score == pytest.approx(0.2, abs=0.01)
    assert mastery.attempts == 1
    assert mastery.next_review_at is not None


@pytest.mark.asyncio
async def test_mastery_clamped_at_one(student_service: StudentModelService):
    req = CreateStudentRequest(
        external_id="stu004",
        name="Sneha Patel",
        grade="7",
        segment="school",
        tenant_id="test-tenant",
    )
    student = await student_service.get_or_create_student(req)

    for _ in range(6):
        await student_service.update_concept_mastery(
            student_id=student.id,
            tenant_id="test-tenant",
            req=UpdateMasteryRequest(
                concept_id="sci_photosynthesis",
                delta_score=0.25,
                reasoning_correct=True,
            ),
        )

    mastery = await student_service.update_concept_mastery(
        student_id=student.id,
        tenant_id="test-tenant",
        req=UpdateMasteryRequest(
            concept_id="sci_photosynthesis",
            delta_score=0.25,
            reasoning_correct=True,
        ),
    )
    assert mastery.mastery_score <= 1.0


@pytest.mark.asyncio
async def test_sm2_quality_mapping(student_service: StudentModelService):
    """Higher delta + reasoning_correct should produce longer spaced intervals."""
    high_quality = student_service._score_to_sr_quality(0.25, True)
    low_quality = student_service._score_to_sr_quality(0.0, False)
    assert high_quality > low_quality
    assert high_quality == 5
    assert low_quality == 2
