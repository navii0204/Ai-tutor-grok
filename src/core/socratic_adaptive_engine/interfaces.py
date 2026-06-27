"""Abstract interfaces for the Socratic + Adaptive engine.

Any new tutoring strategy (Bloom-based, Montessori-style, etc.) can implement
SocraticEngineInterface without touching the rest of the system.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class DialogueTurn:
    role: str  # "student" | "tutor"
    content: str
    concept_ids: list[str] = field(default_factory=list)
    reasoning_quality: float = 0.0
    was_answer_given: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class AdaptiveHint:
    hint_text: str
    hint_level: int  # 1 = most abstract, 5 = most concrete
    concept_id: str
    prerequisite_gap: str | None = None


@dataclass
class SocraticResponse:
    content: str
    is_question: bool
    hint: AdaptiveHint | None
    detected_misconception: str | None
    focus_cue: str | None           # optional mind-body alignment prompt
    reflection_prompt: str | None   # ethical/meta reflection
    mastery_delta: float = 0.0
    reasoning_correct: bool = False


class SocraticEngineInterface(ABC):
    """Core contract every Socratic engine implementation must satisfy."""

    @abstractmethod
    async def respond(
        self,
        student_id: str,
        student_message: str,
        history: list[DialogueTurn],
        concept_id: str,
        student_context: dict[str, Any],
    ) -> SocraticResponse:
        """Generate a Socratic response. MUST NOT directly give the answer."""
        ...

    @abstractmethod
    async def generate_opening_question(
        self,
        concept_id: str,
        student_context: dict[str, Any],
    ) -> str:
        """Generate the first inquiry question for a concept."""
        ...

    @abstractmethod
    async def detect_misconception(
        self, student_message: str, concept_id: str
    ) -> str | None:
        """Identify common misconceptions in the student's response."""
        ...
