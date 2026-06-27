"""CurriculumRegistry — plugin registry for all curriculum segments.

New segments are registered once at startup — no code changes to core.

Usage:
    registry = CurriculumRegistry()
    registry.register(SchoolCurriculumPlugin())
    registry.register(JEECurriculumPlugin())
    plugin = registry.get("school")
"""

from __future__ import annotations

from src.core.logging_config import get_logger
from .interfaces import ConceptNode, CurriculumPlugin

log = get_logger(__name__)


class CurriculumRegistry:
    def __init__(self) -> None:
        self._plugins: dict[str, CurriculumPlugin] = {}

    def register(self, plugin: CurriculumPlugin) -> None:
        self._plugins[plugin.segment_id] = plugin
        log.info("curriculum_plugin_registered", segment=plugin.segment_id)

    def get(self, segment_id: str) -> CurriculumPlugin:
        if segment_id not in self._plugins:
            raise KeyError(f"No curriculum plugin registered for segment '{segment_id}'")
        return self._plugins[segment_id]

    def list_segments(self) -> list[str]:
        return list(self._plugins.keys())

    def find_concept(self, concept_id: str, segment_id: str) -> ConceptNode | None:
        plugin = self._plugins.get(segment_id)
        return plugin.get_concept(concept_id) if plugin else None
