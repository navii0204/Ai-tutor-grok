"""Parent API — weekly holistic growth reports in simple, story-like language."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException

from src.api.dependencies import AnalyticsDep, LLMDep, StudentServiceDep

router = APIRouter()


@router.get("/report/{student_id}")
async def weekly_parent_report(
    student_id: str,
    service: StudentServiceDep,
    analytics: AnalyticsDep,
    llm: LLMDep,
) -> dict[str, Any]:
    """Generate a warm, story-style weekly report for parents.

    Avoids jargon. Highlights growth, effort, and one specific reasoning moment.
    Includes a simple at-home suggestion aligned to the week's learning.
    """
    student = await service.get_student(student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    summary = analytics.student_growth_summary(student)
    m = student.holistic_markers

    # Compose narrative context for LLM
    context = (
        f"Student: {student.name}, Grade {student.grade}\n"
        f"This week: {summary.concepts_mastered} concepts mastered, "
        f"{m.total_sessions if m else 0} sessions, "
        f"{m.streak_days if m else 0}-day streak\n"
        f"Reasoning quality: {summary.avg_reasoning:.0%}\n"
        f"Reflection depth: {summary.avg_reflection:.0%}\n"
        f"Focus level: {summary.avg_focus:.0%}\n"
        f"Trend: {summary.mastery_trend}\n"
        f"Growth highlight: {summary.highlight}"
    )

    system_prompt = (
        "You are writing a warm, encouraging weekly learning report for Indian parents. "
        "Use simple, positive language (no jargon). "
        "Structure: 1) What your child explored this week (2 sentences). "
        "2) A specific moment of great thinking (with an example). "
        "3) Their growth in character/values/reflection. "
        "4) One simple activity to try at home together. "
        "Keep it under 200 words. End with an encouraging sentence."
    )

    narrative = await llm.chat(
        system_prompt=system_prompt,
        messages=[{"role": "user", "content": f"Write a parent report:\n{context}"}],
        temperature=0.7,
    )

    return {
        "student_name": student.name,
        "grade": student.grade,
        "streak_days": m.streak_days if m else 0,
        "concepts_mastered": summary.concepts_mastered,
        "mastery_trend": summary.mastery_trend,
        "avg_focus": summary.avg_focus,
        "narrative_report": narrative,
        "needs_support": summary.needs_support,
    }


@router.get("/progress/{student_id}/summary")
async def parent_progress_summary(
    student_id: str,
    service: StudentServiceDep,
    analytics: AnalyticsDep,
) -> dict[str, Any]:
    """Lightweight progress card — suitable for a mobile notification."""
    student = await service.get_student(student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    summary = analytics.student_growth_summary(student)
    return {
        "name": student.name,
        "streak": summary.streak_days,
        "concepts_mastered": summary.concepts_mastered,
        "trend": summary.mastery_trend,
        "highlight": summary.highlight,
    }
