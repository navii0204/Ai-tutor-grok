"""Curriculum plugin interface — any segment (school, JEE, engineering) must implement this."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class LearningObjective:
    id: str
    description: str
    bloom_level: str  # remember | understand | apply | analyze | evaluate | create
    nep_competency: str | None = None  # NEP 2020 competency mapping
    ethical_dimension: str | None = None


@dataclass
class ConceptNode:
    id: str
    name: str
    description: str
    subject: str
    grade: str
    segment: str
    prerequisites: list[str] = field(default_factory=list)
    objectives: list[LearningObjective] = field(default_factory=list)
    real_world_connections: list[str] = field(default_factory=list)
    india_context_examples: list[str] = field(default_factory=list)
    mastery_keywords: list[str] = field(default_factory=list)
    ethical_scenarios: list[str] = field(default_factory=list)
    estimated_minutes: int = 20
    tags: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


class CurriculumPlugin(ABC):
    """Interface every curriculum segment plugin must implement.

    Extensibility: Register new plugins via CurriculumRegistry — no core code changes.
    """

    @property
    @abstractmethod
    def segment_id(self) -> str:
        """Unique identifier: 'school', 'jee', 'engineering', etc."""
        ...

    @property
    @abstractmethod
    def supported_grades(self) -> list[str]:
        ...

    @abstractmethod
    def get_concept(self, concept_id: str) -> ConceptNode | None:
        ...

    @abstractmethod
    def list_concepts(self, grade: str, subject: str | None = None) -> list[ConceptNode]:
        ...

    @abstractmethod
    def get_prerequisites(self, concept_id: str) -> list[str]:
        ...

    @abstractmethod
    def get_next_concepts(self, concept_id: str, mastered: set[str]) -> list[str]:
        ...

    @abstractmethod
    def get_project_suggestions(self, concept_ids: list[str], grade: str) -> list[dict[str, Any]]:
        """Return project-based learning suggestions aligned to concepts."""
        ...

    def search_concepts(self, query: str, grade: str | None = None) -> list[ConceptNode]:
        """Optional: full-text search across concepts. Override for efficiency."""
        all_concepts = self.list_concepts(grade or "", None) if grade else []
        q = query.lower()
        return [c for c in all_concepts if q in c.name.lower() or q in c.description.lower()]
