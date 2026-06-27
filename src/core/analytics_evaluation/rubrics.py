"""Cognitive and ethical reasoning rubrics for evaluating student responses.

Rubrics are inspired by Bloom's taxonomy + NEP 2020 competency framework.
The LLM acts as evaluator using structured prompts; results update mastery.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from src.core.logging_config import get_logger
from src.core.multimodal_context.llm_provider import LLMProvider

log = get_logger(__name__)


@dataclass
class RubricDimension:
    name: str
    description: str
    weight: float  # sum of all weights in a rubric should = 1.0
    indicators: list[str]  # bullet points of what "good" looks like


@dataclass
class CognitiveRubric:
    concept_id: str
    dimensions: list[RubricDimension] = field(default_factory=list)

    @classmethod
    def default(cls, concept_id: str) -> "CognitiveRubric":
        return cls(
            concept_id=concept_id,
            dimensions=[
                RubricDimension(
                    name="Conceptual Understanding",
                    description="Can the student articulate the core idea in their own words?",
                    weight=0.35,
                    indicators=[
                        "Uses own words, not verbatim repetition",
                        "Gives at least one accurate example",
                        "Connects to a related concept",
                    ],
                ),
                RubricDimension(
                    name="Reasoning Quality",
                    description="Does the student show step-by-step reasoning?",
                    weight=0.35,
                    indicators=[
                        "Explains WHY not just WHAT",
                        "Considers cause and effect",
                        "Identifies patterns or rules",
                    ],
                ),
                RubricDimension(
                    name="Application",
                    description="Can the student apply the concept to a new situation?",
                    weight=0.20,
                    indicators=[
                        "Transfers to a novel problem",
                        "Uses the concept in a real-world context",
                    ],
                ),
                RubricDimension(
                    name="Metacognition",
                    description="Is the student aware of their own thinking?",
                    weight=0.10,
                    indicators=[
                        "Identifies what they still don't understand",
                        "Asks follow-up questions",
                        "Reflects on their reasoning process",
                    ],
                ),
            ],
        )


@dataclass
class EthicalRubric:
    scenario: str
    dimensions: list[RubricDimension] = field(default_factory=list)

    @classmethod
    def default(cls, scenario: str) -> "EthicalRubric":
        return cls(
            scenario=scenario,
            dimensions=[
                RubricDimension(
                    name="Perspective Taking",
                    description="Does the student consider multiple stakeholders?",
                    weight=0.4,
                    indicators=["Names at least 2 affected parties", "Describes impact on each"],
                ),
                RubricDimension(
                    name="Values Articulation",
                    description="Can the student name and justify the values at stake?",
                    weight=0.35,
                    indicators=["Names a relevant value (fairness, honesty, care)", "Explains why that value matters here"],
                ),
                RubricDimension(
                    name="Action & Consequence",
                    description="Does the student think through consequences?",
                    weight=0.25,
                    indicators=["Considers short and long-term effects", "Acknowledges trade-offs"],
                ),
            ],
        )


@dataclass
class RubricScore:
    total: float  # 0.0–1.0
    dimension_scores: dict[str, float]
    feedback_points: list[str]
    strength: str
    growth_area: str


class RubricEvaluator:
    """Uses LLM to score student responses against a rubric.

    Scalability note: For async batch evaluation (e.g., end-of-day analytics),
    run this in a background worker pool. The LLM call is the bottleneck.
    """

    def __init__(self, llm: LLMProvider) -> None:
        self._llm = llm

    async def evaluate_cognitive(
        self, student_response: str, rubric: CognitiveRubric, concept_name: str
    ) -> RubricScore:
        prompt = self._build_cognitive_prompt(student_response, rubric, concept_name)
        result = await self._llm.chat(
            system_prompt=self._evaluator_system_prompt(),
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
        )
        return self._parse_rubric_result(result, rubric.dimensions)

    async def evaluate_ethical(
        self, student_response: str, rubric: EthicalRubric
    ) -> RubricScore:
        prompt = self._build_ethical_prompt(student_response, rubric)
        result = await self._llm.chat(
            system_prompt=self._evaluator_system_prompt(),
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
        )
        return self._parse_rubric_result(result, rubric.dimensions)

    def _evaluator_system_prompt(self) -> str:
        return (
            "You are an expert educational evaluator for Indian school students (Grades 6–12). "
            "Score each rubric dimension from 0.0 to 1.0. Be fair, encouraging, and specific. "
            "Output ONLY valid JSON with keys: dimension_scores (dict), feedback_points (list of str), "
            "strength (str), growth_area (str)."
        )

    def _build_cognitive_prompt(
        self, response: str, rubric: CognitiveRubric, concept_name: str
    ) -> str:
        dims = "\n".join(
            f"- {d.name} (weight={d.weight}): {d.description}\n  Indicators: {', '.join(d.indicators)}"
            for d in rubric.dimensions
        )
        return (
            f"Concept: {concept_name}\n\n"
            f"Student's response:\n{response}\n\n"
            f"Rubric dimensions:\n{dims}\n\n"
            "Score each dimension 0.0–1.0 and return JSON."
        )

    def _build_ethical_prompt(self, response: str, rubric: EthicalRubric) -> str:
        dims = "\n".join(
            f"- {d.name}: {d.description}"
            for d in rubric.dimensions
        )
        return (
            f"Ethical scenario: {rubric.scenario}\n\n"
            f"Student's response:\n{response}\n\n"
            f"Rubric dimensions:\n{dims}\n\n"
            "Score each dimension 0.0–1.0 and return JSON."
        )

    def _parse_rubric_result(
        self, llm_output: str, dimensions: list[RubricDimension]
    ) -> RubricScore:
        import json, re
        try:
            match = re.search(r"\{.*\}", llm_output, re.DOTALL)
            data: dict[str, Any] = json.loads(match.group()) if match else {}
        except (json.JSONDecodeError, AttributeError):
            data = {}

        dim_scores: dict[str, float] = data.get("dimension_scores", {})
        total = sum(
            float(dim_scores.get(d.name, 0.5)) * d.weight for d in dimensions
        )
        return RubricScore(
            total=round(total, 3),
            dimension_scores={d.name: float(dim_scores.get(d.name, 0.5)) for d in dimensions},
            feedback_points=data.get("feedback_points", []),
            strength=data.get("strength", ""),
            growth_area=data.get("growth_area", ""),
        )
