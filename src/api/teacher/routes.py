"""Teacher API — classroom insights, lesson generation, and student monitoring."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from src.api.dependencies import (
    AnalyticsDep,
    CurriculumDep,
    LLMDep,
    StudentServiceDep,
    SettingsDep,
)

router = APIRouter()


@router.get("/classroom/{tenant_id}/grade/{grade}/insights")
async def classroom_insights(
    tenant_id: str,
    grade: str,
    service: StudentServiceDep,
    analytics: AnalyticsDep,
) -> dict[str, Any]:
    """Real-time classroom mastery heatmap for a teacher's dashboard."""
    students = await service.list_students(tenant_id)
    grade_students = [s for s in students if s.grade == grade]
    heatmap = analytics.classroom_heatmap(grade_students, tenant_id, grade)
    return {
        "grade": grade,
        "student_count": len(grade_students),
        "class_averages": heatmap.class_averages,
        "at_risk_students": heatmap.at_risk_students,
        "weak_concepts": heatmap.weak_concepts,
        "top_concepts": heatmap.top_concepts,
        "generated_at": heatmap.generated_at.isoformat(),
    }


@router.get("/student/{student_id}/growth")
async def student_growth(
    student_id: str,
    service: StudentServiceDep,
    analytics: AnalyticsDep,
) -> dict[str, Any]:
    student = await service.get_student(student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    summary = analytics.student_growth_summary(student)
    return {
        "student_id": summary.student_id,
        "name": summary.name,
        "mastery_trend": summary.mastery_trend,
        "concepts_mastered": summary.concepts_mastered,
        "avg_reasoning": summary.avg_reasoning,
        "avg_reflection": summary.avg_reflection,
        "streak_days": summary.streak_days,
        "needs_support": summary.needs_support,
        "highlight": summary.highlight,
    }


class LessonPlanRequest(BaseModel):
    concept_id: str
    grade: str
    segment: str = "school"
    duration_minutes: int = 45
    focus_area: str = "conceptual_understanding"


@router.post("/lesson-plan")
async def generate_lesson_plan(
    req: LessonPlanRequest,
    curriculum: CurriculumDep,
    llm: LLMDep,
) -> dict[str, Any]:
    """Generate a Socratic lesson plan for a concept, with discussion questions and activities."""
    plugin = curriculum.get(req.segment)
    concept = plugin.get_concept(req.concept_id)
    if not concept:
        raise HTTPException(status_code=404, detail=f"Concept '{req.concept_id}' not found")

    projects = plugin.get_project_suggestions([req.concept_id], req.grade)

    system_prompt = (
        "You are an expert curriculum designer for Indian schools following NEP 2020. "
        "Create a Socratic, activity-based lesson plan. Focus on inquiry questions, "
        "not lectures. Include mind-body warm-up, ethical connections, and reflection. "
        "Format: JSON with keys: warm_up, inquiry_questions, activities, "
        "ethical_discussion, reflection_prompt, assessment_ideas."
    )
    user_prompt = (
        f"Create a {req.duration_minutes}-min lesson plan for:\n"
        f"Concept: {concept.name}\n"
        f"Grade: {req.grade}\n"
        f"Description: {concept.description}\n"
        f"India context: {'; '.join(concept.india_context_examples[:2])}\n"
        f"Real-world connections: {'; '.join(concept.real_world_connections[:3])}\n"
        f"Focus area: {req.focus_area}"
    )

    plan_text = await llm.chat(
        system_prompt=system_prompt,
        messages=[{"role": "user", "content": user_prompt}],
        temperature=0.6,
    )

    return {
        "concept": concept.name,
        "grade": req.grade,
        "duration_minutes": req.duration_minutes,
        "lesson_plan_text": plan_text,
        "suggested_projects": projects[:2],
        "mastery_keywords": concept.mastery_keywords,
    }


@router.post("/rubric/generate")
async def generate_assessment_rubric(
    concept_id: str,
    grade: str,
    segment: str = "school",
    curriculum: CurriculumDep = ...,
    llm: LLMDep = ...,
) -> dict[str, Any]:
    plugin = curriculum.get(segment)
    concept = plugin.get_concept(concept_id)
    if not concept:
        raise HTTPException(status_code=404, detail="Concept not found")

    prompt = (
        f"Create a detailed assessment rubric for '{concept.name}' (Grade {grade}). "
        f"Use Bloom's taxonomy levels. Include 4 dimensions with 3 performance levels each "
        f"(Beginning, Developing, Proficient). Return valid JSON."
    )
    rubric_text = await llm.chat(
        system_prompt="You are an expert educational assessment designer for Indian schools.",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.4,
    )
    return {"concept": concept.name, "rubric": rubric_text}
