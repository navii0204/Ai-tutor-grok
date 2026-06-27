"""HolisticMetricsEngine — computes ecosystem-wide analytics.

Produces:
  - Per-student growth trajectories
  - Classroom mastery heatmaps
  - Equity analytics (identify students needing support)
  - NEP compliance summaries
  - Teacher workload metrics

Scalability note: For >1k students, run these as nightly Celery tasks
that materialise results into a read-optimised analytics table (or ClickHouse).
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from typing import Any

from src.core.student_model.models import HolisticMarkers, StudentProfile


@dataclass
class StudentGrowthSummary:
    student_id: str
    name: str
    grade: str
    mastery_trend: str          # "growing" | "plateau" | "declining"
    concepts_mastered: int
    avg_reasoning: float
    avg_reflection: float
    avg_focus: float
    streak_days: int
    needs_support: bool
    highlight: str              # one-sentence growth story for parent report


@dataclass
class ClassroomHeatmap:
    tenant_id: str
    grade: str
    concept_mastery: dict[str, dict[str, float]]  # concept_id → {student_id: score}
    class_averages: dict[str, float]              # concept_id → average
    at_risk_students: list[str]                   # student_ids below threshold
    top_concepts: list[str]
    weak_concepts: list[str]
    generated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class NEPComplianceReport:
    tenant_id: str
    period: str
    competencies_addressed: list[str]
    project_based_hours: int
    ethical_moments_count: int
    holistic_markers_avg: dict[str, float]
    recommendations: list[str]


class HolisticMetricsEngine:
    """Computes analytics across students and classrooms."""

    def student_growth_summary(self, student: StudentProfile) -> StudentGrowthSummary:
        m = student.holistic_markers
        if not m:
            return StudentGrowthSummary(
                student_id=student.id,
                name=student.name,
                grade=student.grade,
                mastery_trend="unknown",
                concepts_mastered=0,
                avg_reasoning=0.0,
                avg_reflection=0.0,
                avg_focus=0.0,
                streak_days=0,
                needs_support=True,
                highlight="Just getting started on their learning journey.",
            )

        mastered = sum(
            1 for cm in (student.concept_masteries or []) if cm.mastery_score >= 0.7
        )
        trend = self._compute_trend(m)
        needs_support = (
            m.avg_reasoning_quality < 0.4
            or m.avg_focus_signal < 0.3
            or m.streak_days == 0
        )

        return StudentGrowthSummary(
            student_id=student.id,
            name=student.name,
            grade=student.grade,
            mastery_trend=trend,
            concepts_mastered=mastered,
            avg_reasoning=round(m.avg_reasoning_quality, 2),
            avg_reflection=round(m.avg_reflection_depth, 2),
            avg_focus=round(m.avg_focus_signal, 2),
            streak_days=m.streak_days,
            needs_support=needs_support,
            highlight=self._build_highlight(student.name, m, mastered),
        )

    def classroom_heatmap(
        self, students: list[StudentProfile], tenant_id: str, grade: str
    ) -> ClassroomHeatmap:
        concept_mastery: dict[str, dict[str, float]] = defaultdict(dict)
        for student in students:
            for cm in (student.concept_masteries or []):
                concept_mastery[cm.concept_id][student.id] = cm.mastery_score

        class_avgs = {
            cid: sum(scores.values()) / len(scores)
            for cid, scores in concept_mastery.items()
        }

        at_risk = [
            s.id
            for s in students
            if s.holistic_markers and s.holistic_markers.avg_reasoning_quality < 0.35
        ]

        sorted_concepts = sorted(class_avgs.items(), key=lambda x: x[1])
        weak = [c for c, _ in sorted_concepts[:3]]
        top = [c for c, _ in sorted_concepts[-3:]]

        return ClassroomHeatmap(
            tenant_id=tenant_id,
            grade=grade,
            concept_mastery=dict(concept_mastery),
            class_averages=class_avgs,
            at_risk_students=at_risk,
            top_concepts=top,
            weak_concepts=weak,
        )

    def nep_compliance_report(
        self, students: list[StudentProfile], tenant_id: str, period: str
    ) -> NEPComplianceReport:
        total_ethical = sum(
            (s.holistic_markers.ethical_moments_count if s.holistic_markers else 0)
            for s in students
        )
        avg_reflection = (
            sum(s.holistic_markers.avg_reflection_depth for s in students if s.holistic_markers)
            / max(len(students), 1)
        )
        competencies = [
            "Critical Thinking",
            "Communication",
            "Collaboration",
            "Creativity",
            "Ethical Reasoning",
        ]
        if avg_reflection > 0.5:
            competencies.append("Reflective Practice")

        project_hours = sum(
            (s.holistic_markers.total_learning_minutes // 60 // 3 if s.holistic_markers else 0)
            for s in students
        )

        return NEPComplianceReport(
            tenant_id=tenant_id,
            period=period,
            competencies_addressed=competencies,
            project_based_hours=project_hours,
            ethical_moments_count=total_ethical,
            holistic_markers_avg={
                "reasoning": round(
                    sum(s.holistic_markers.avg_reasoning_quality for s in students if s.holistic_markers)
                    / max(len(students), 1),
                    2,
                ),
                "reflection": round(avg_reflection, 2),
            },
            recommendations=self._nep_recommendations(avg_reflection, total_ethical, students),
        )

    def _compute_trend(self, m: HolisticMarkers) -> str:
        if m.learning_velocity > 0.6 and m.avg_reasoning_quality > 0.5:
            return "growing"
        if m.learning_velocity < 0.2 or m.total_sessions < 3:
            return "declining"
        return "plateau"

    def _build_highlight(
        self, name: str, m: HolisticMarkers, mastered: int
    ) -> str:
        parts = []
        if mastered > 0:
            parts.append(f"{name} has mastered {mastered} concept(s)")
        if m.streak_days >= 3:
            parts.append(f"maintained a {m.streak_days}-day learning streak")
        if m.avg_reasoning_quality > 0.6:
            parts.append("shown strong reasoning skills")
        if m.ethical_moments_count > 0:
            parts.append(f"engaged in {m.ethical_moments_count} ethical reflection(s)")
        if not parts:
            return f"{name} is beginning their learning journey."
        return f"{name} has " + ", and ".join(parts) + "."

    def _nep_recommendations(
        self,
        avg_reflection: float,
        ethical_count: int,
        students: list[StudentProfile],
    ) -> list[str]:
        recs = []
        if avg_reflection < 0.4:
            recs.append("Increase reflective journaling prompts at end of each session.")
        if ethical_count < len(students):
            recs.append("Incorporate more ethical scenario discussions in STEM topics.")
        at_risk = [
            s.name
            for s in students
            if s.holistic_markers and s.holistic_markers.avg_focus_signal < 0.3
        ]
        if at_risk:
            recs.append(
                f"Students needing focus support: {', '.join(at_risk[:5])}."
                " Consider shorter sessions or more interactive simulator tasks."
            )
        return recs
