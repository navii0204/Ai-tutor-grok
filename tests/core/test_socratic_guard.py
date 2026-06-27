"""Tests for the Socratic guard — critical safety layer."""

from __future__ import annotations

import pytest

from src.core.socratic_adaptive_engine.guards import SocraticGuard


def test_guard_blocks_direct_answer():
    guard = SocraticGuard()
    result = guard.check("The answer is 42.")
    assert not result.passed
    assert "Direct answer" in result.reason


def test_guard_blocks_solution_reveal():
    guard = SocraticGuard()
    result = guard.check("Here is the solution: x = 5.")
    assert not result.passed


def test_guard_blocks_no_question():
    guard = SocraticGuard()
    result = guard.check("Photosynthesis converts sunlight to glucose.")
    assert not result.passed
    assert "lacks an inquiry question" in result.reason


def test_guard_passes_good_socratic():
    guard = SocraticGuard()
    result = guard.check(
        "Interesting thinking! What do you notice about the pattern here? "
        "What would change if we doubled the input?"
    )
    assert result.passed


def test_guard_sanitised_text_contains_question():
    guard = SocraticGuard()
    result = guard.check("The answer is x=5.")
    assert "?" in result.sanitised_text
