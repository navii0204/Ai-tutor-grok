"""ContextBuilder — assembles the full multimodal context for LLM calls.

Combines: student model state + concept metadata + simulator state + vision output.
This single object is passed into every Socratic dialogue turn so the LLM has
full situational awareness.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from src.core.curriculum_mapper.interfaces import ConceptNode
from src.core.student_model.models import HolisticMarkers, StudentProfile


@dataclass
class SimulatorStateSnapshot:
    simulator_id: str
    state_description: str  # human-readable summary for LLM prompt
    raw_state: dict[str, Any] = field(default_factory=dict)


@dataclass
class VisionOutput:
    engagement_score: float    # 0.0–1.0
    detected_emotion: str      # "focused" | "confused" | "bored" | "excited"
    notes: str = ""


@dataclass
class MultimodalContext:
    """All contextual signals for a single dialogue turn."""

    student_name: str
    grade: str
    language: str
    segment: str
    mastery_score: float
    confidence: float
    learning_velocity: str
    concept_id: str
    concept_name: str
    concept_description: str
    mastery_keywords: list[str]
    india_context_examples: list[str]
    session_type: str
    simulator_state: str = "None"
    vision_output: VisionOutput | None = None
    holistic_markers: dict[str, Any] = field(default_factory=dict)
    extra: dict[str, Any] = field(default_factory=dict)

    def to_llm_dict(self) -> dict[str, Any]:
        return {
            "student_name": self.student_name,
            "grade": self.grade,
            "language": self.language,
            "segment": self.segment,
            "mastery_score": self.mastery_score,
            "confidence": self.confidence,
            "learning_velocity": self.learning_velocity,
            "concept_id": self.concept_id,
            "concept_name": self.concept_name,
            "concept_description": self.concept_description,
            "mastery_keywords": self.mastery_keywords,
            "session_type": self.session_type,
            "simulator_state": self.simulator_state,
        }


class ContextBuilder:
    """Builds MultimodalContext from individual domain objects."""

    def build(
        self,
        student: StudentProfile,
        concept: ConceptNode,
        mastery_score: float,
        confidence: float,
        session_type: str = "chat",
        simulator_snapshot: SimulatorStateSnapshot | None = None,
        vision_output: VisionOutput | None = None,
    ) -> MultimodalContext:
        velocity = self._velocity_label(student.holistic_markers)
        markers_dict: dict[str, Any] = {}
        if student.holistic_markers:
            m = student.holistic_markers
            markers_dict = {
                "avg_focus_signal": m.avg_focus_signal,
                "avg_reflection_depth": m.avg_reflection_depth,
                "resilience_score": m.resilience_score,
            }

        sim_state = "None"
        if simulator_snapshot:
            sim_state = simulator_snapshot.state_description

        return MultimodalContext(
            student_name=student.name,
            grade=student.grade,
            language=student.language,
            segment=student.segment,
            mastery_score=mastery_score,
            confidence=confidence,
            learning_velocity=velocity,
            concept_id=concept.id,
            concept_name=concept.name,
            concept_description=concept.description,
            mastery_keywords=concept.mastery_keywords,
            india_context_examples=concept.india_context_examples,
            session_type=session_type,
            simulator_state=sim_state,
            vision_output=vision_output,
            holistic_markers=markers_dict,
        )

    def _velocity_label(self, markers: HolisticMarkers | None) -> str:
        if not markers:
            return "moderate"
        v = markers.learning_velocity
        if v > 0.7:
            return "fast"
        if v > 0.4:
            return "moderate"
        return "needs support"
