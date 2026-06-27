"""Admin/School API — equity analytics, NEP reports, and curriculum management."""

from __future__ import annotations

from datetime import date
from typing import Any

from fastapi import APIRouter, HTTPException

from src.api.dependencies import AnalyticsDep, CurriculumDep, StudentServiceDep

router = APIRouter()


@router.get("/tenant/{tenant_id}/nep-report")
async def nep_compliance_report(
    tenant_id: str,
    period: str = "2024-Q1",
    service: StudentServiceDep = ...,
    analytics: AnalyticsDep = ...,
) -> dict[str, Any]:
    students = await service.list_students(tenant_id, limit=500)
    report = analytics.nep_report(students, tenant_id, period)
    return {
        "tenant_id": tenant_id,
        "period": report.period,
        "competencies_addressed": report.competencies_addressed,
        "project_based_hours": report.project_based_hours,
        "ethical_moments_count": report.ethical_moments_count,
        "holistic_markers_avg": report.holistic_markers_avg,
        "recommendations": report.recommendations,
    }


@router.get("/tenant/{tenant_id}/equity-report")
async def equity_analytics(
    tenant_id: str,
    service: StudentServiceDep = ...,
    analytics: AnalyticsDep = ...,
) -> dict[str, Any]:
    """Identify at-risk students and equity gaps across grades."""
    students = await service.list_students(tenant_id, limit=500)
    by_grade: dict[str, list[Any]] = {}
    for s in students:
        by_grade.setdefault(s.grade, []).append(s)

    grade_summaries = []
    for grade, grade_students in by_grade.items():
        heatmap = analytics.classroom_heatmap(grade_students, tenant_id, grade)
        grade_summaries.append({
            "grade": grade,
            "student_count": len(grade_students),
            "at_risk_count": len(heatmap.at_risk_students),
            "weak_concepts": heatmap.weak_concepts,
        })

    all_at_risk = [
        s.id
        for s in students
        if s.holistic_markers and s.holistic_markers.avg_reasoning_quality < 0.35
    ]

    return {
        "tenant_id": tenant_id,
        "total_students": len(students),
        "at_risk_count": len(all_at_risk),
        "grade_summaries": grade_summaries,
    }


@router.get("/curriculum/{segment}/concepts")
async def list_curriculum(
    segment: str,
    grade: str | None = None,
    subject: str | None = None,
    curriculum: CurriculumDep = ...,
) -> dict[str, Any]:
    plugin = curriculum.get(segment)
    concepts = plugin.list_concepts(grade or "", subject)
    return {
        "segment": segment,
        "grade": grade,
        "concepts": [
            {
                "id": c.id,
                "name": c.name,
                "subject": c.subject,
                "grade": c.grade,
                "prerequisites": c.prerequisites,
                "estimated_minutes": c.estimated_minutes,
            }
            for c in concepts
        ],
    }
