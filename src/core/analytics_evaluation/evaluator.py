"""AnalyticsEvaluator — top-level facade combining rubric evaluation + metrics."""

from __future__ import annotations

from typing import Any

from src.core.multimodal_context.llm_provider import LLMProvider
from src.core.student_model.models import StudentProfile
from .metrics import ClassroomHeatmap, HolisticMetricsEngine, NEPComplianceReport, StudentGrowthSummary
from .rubrics import CognitiveRubric, EthicalRubric, RubricEvaluator, RubricScore


class AnalyticsEvaluator:
    """Unified evaluation interface for all ecosystem layers."""

    def __init__(self, llm: LLMProvider) -> None:
        self._rubric_evaluator = RubricEvaluator(llm)
        self._metrics_engine = HolisticMetricsEngine()

    async def evaluate_student_response(
        self,
        student_response: str,
        concept_id: str,
        concept_name: str,
    ) -> RubricScore:
        rubric = CognitiveRubric.default(concept_id)
        return await self._rubric_evaluator.evaluate_cognitive(
            student_response, rubric, concept_name
        )

    async def evaluate_ethical_response(
        self, student_response: str, scenario: str
    ) -> RubricScore:
        rubric = EthicalRubric.default(scenario)
        return await self._rubric_evaluator.evaluate_ethical(student_response, rubric)

    def student_growth_summary(self, student: StudentProfile) -> StudentGrowthSummary:
        return self._metrics_engine.student_growth_summary(student)

    def classroom_heatmap(
        self, students: list[StudentProfile], tenant_id: str, grade: str
    ) -> ClassroomHeatmap:
        return self._metrics_engine.classroom_heatmap(students, tenant_id, grade)

    def nep_report(
        self, students: list[StudentProfile], tenant_id: str, period: str
    ) -> NEPComplianceReport:
        return self._metrics_engine.nep_compliance_report(students, tenant_id, period)
