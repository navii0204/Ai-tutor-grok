"""Tests for school and JEE curriculum plugins."""

from __future__ import annotations

import pytest

from src.core.curriculum_mapper.registry import CurriculumRegistry
from src.plugins.jee.curriculum import JEECurriculumPlugin
from src.plugins.school.curriculum import SchoolCurriculumPlugin


@pytest.fixture
def registry() -> CurriculumRegistry:
    reg = CurriculumRegistry()
    reg.register(SchoolCurriculumPlugin())
    reg.register(JEECurriculumPlugin())
    return reg


def test_school_plugin_registered(registry: CurriculumRegistry):
    plugin = registry.get("school")
    assert plugin.segment_id == "school"


def test_jee_plugin_registered(registry: CurriculumRegistry):
    plugin = registry.get("jee")
    assert plugin.segment_id == "jee"


def test_school_concept_exists(registry: CurriculumRegistry):
    plugin = registry.get("school")
    concept = plugin.get_concept("sci_photosynthesis")
    assert concept is not None
    assert concept.grade == "7"
    assert concept.subject == "science"
    assert len(concept.india_context_examples) > 0


def test_prerequisites_resolved(registry: CurriculumRegistry):
    plugin = registry.get("school")
    prereqs = plugin.get_prerequisites("math_fractions_operations")
    assert "math_fractions_basic" in prereqs


def test_next_concepts_after_mastery(registry: CurriculumRegistry):
    plugin = registry.get("school")
    mastered = {"math_fractions_basic"}
    next_c = plugin.get_next_concepts("math_fractions_basic", mastered)
    assert "math_fractions_operations" in next_c


def test_project_suggestions(registry: CurriculumRegistry):
    plugin = registry.get("school")
    projects = plugin.get_project_suggestions(["ct_loops", "ct_conditionals"], "7")
    assert len(projects) > 0
    assert any("maze" in p["name"].lower() for p in projects)


def test_jee_kinematics_chain(registry: CurriculumRegistry):
    plugin = registry.get("jee")
    prereqs = plugin.get_prerequisites("jee_kinematics_2d")
    assert "jee_kinematics_1d" in prereqs


def test_unknown_segment_raises(registry: CurriculumRegistry):
    with pytest.raises(KeyError):
        registry.get("unknown_segment")


def test_concept_has_ethical_dimension(registry: CurriculumRegistry):
    plugin = registry.get("school")
    concept = plugin.get_concept("sci_photosynthesis")
    assert any("ethical" in s.lower() or "forest" in s.lower() for s in concept.ethical_scenarios)
