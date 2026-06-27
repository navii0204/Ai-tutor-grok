"""AdaptivePathPlanner — decides WHAT to teach next based on student state.

Uses concept mastery + prerequisite graph + spaced repetition schedule to
build a personalized micro-learning path for each session.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol


class ConceptGraphProtocol(Protocol):
    def get_prerequisites(self, concept_id: str) -> list[str]: ...
    def get_next_concepts(self, concept_id: str, mastered: set[str]) -> list[str]: ...


@dataclass
class LearningStep:
    concept_id: str
    reason: str          # "prerequisite_gap" | "due_review" | "next_in_path" | "challenge"
    priority: float      # 0.0–1.0, higher = teach first
    hint_level_start: int = 3


class AdaptivePathPlanner:
    """Generates an ordered sequence of micro-learning steps for a session.

    Scalability note: This is CPU-bound and stateless — safe to run in a
    thread pool executor or as a separate microservice for heavy load.
    """

    def __init__(self, concept_graph: ConceptGraphProtocol) -> None:
        self._graph = concept_graph

    def plan_session(
        self,
        target_concept_id: str,
        mastery_map: dict[str, float],
        due_review_ids: list[str],
        max_steps: int = 5,
    ) -> list[LearningStep]:
        steps: list[LearningStep] = []

        # 1. Check prerequisite gaps
        prereqs = self._graph.get_prerequisites(target_concept_id)
        for prereq_id in prereqs:
            score = mastery_map.get(prereq_id, 0.0)
            if score < 0.6:
                steps.append(
                    LearningStep(
                        concept_id=prereq_id,
                        reason="prerequisite_gap",
                        priority=0.9 + (0.6 - score),
                        hint_level_start=4,
                    )
                )

        # 2. Spaced repetition due items
        for review_id in due_review_ids[:2]:
            if review_id != target_concept_id:
                steps.append(
                    LearningStep(
                        concept_id=review_id,
                        reason="due_review",
                        priority=0.7,
                        hint_level_start=2,
                    )
                )

        # 3. Target concept itself
        mastered = {cid for cid, score in mastery_map.items() if score >= 0.7}
        target_score = mastery_map.get(target_concept_id, 0.0)
        steps.append(
            LearningStep(
                concept_id=target_concept_id,
                reason="next_in_path" if target_score < 0.7 else "challenge",
                priority=0.8,
                hint_level_start=3 if target_score < 0.3 else 2,
            )
        )

        # 4. Sort by priority and deduplicate
        seen: set[str] = set()
        unique: list[LearningStep] = []
        for step in sorted(steps, key=lambda s: -s.priority):
            if step.concept_id not in seen:
                seen.add(step.concept_id)
                unique.append(step)

        return unique[:max_steps]

    def suggest_next_after_mastery(
        self, concept_id: str, mastery_map: dict[str, float]
    ) -> list[str]:
        mastered = {cid for cid, score in mastery_map.items() if score >= 0.7}
        return self._graph.get_next_concepts(concept_id, mastered)
