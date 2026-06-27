"""Tests for SocraticDialogueManager with mocked LLM."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from src.core.socratic_adaptive_engine.dialogue_manager import SocraticDialogueManager
from src.core.socratic_adaptive_engine.guards import SocraticGuard
from src.core.socratic_adaptive_engine.interfaces import DialogueTurn


@pytest.fixture
def mock_llm_good():
    llm = AsyncMock()
    llm.chat = AsyncMock(
        return_value=(
            "Great observation! Now, if the plant had no chlorophyll, "
            "what do you think would happen to the glucose production? "
            "What does chlorophyll actually do?"
        )
    )
    return llm


@pytest.fixture
def mock_llm_bad():
    """Simulates an LLM that gives a direct answer (guard should catch this)."""
    llm = AsyncMock()
    llm.chat = AsyncMock(return_value="The answer is glucose and oxygen.")
    return llm


@pytest.mark.asyncio
async def test_socratic_response_contains_question(mock_llm_good):
    engine = SocraticDialogueManager(llm=mock_llm_good)
    response = await engine.respond(
        student_id="stu001",
        student_message="I think plants need sunlight to grow.",
        history=[],
        concept_id="sci_photosynthesis",
        student_context={
            "student_name": "Arjun",
            "grade": "7",
            "mastery_score": 0.2,
            "concept_name": "Photosynthesis",
            "learning_velocity": "moderate",
            "concept_description": "Plants make food using sunlight.",
            "simulator_state": "None",
            "language": "English",
            "session_type": "chat",
        },
    )
    assert response.is_question
    assert "?" in response.content


@pytest.mark.asyncio
async def test_guard_intercepts_bad_llm(mock_llm_bad):
    engine = SocraticDialogueManager(llm=mock_llm_bad)
    response = await engine.respond(
        student_id="stu001",
        student_message="What is made during photosynthesis?",
        history=[],
        concept_id="sci_photosynthesis",
        student_context={
            "student_name": "Priya",
            "grade": "7",
            "mastery_score": 0.1,
            "concept_name": "Photosynthesis",
            "learning_velocity": "moderate",
            "concept_description": "...",
            "simulator_state": "None",
            "language": "English",
            "session_type": "chat",
        },
    )
    # Guard should redirect, and result should still have a question
    assert "?" in response.content
    # The raw "The answer is" should NOT appear in final output
    assert "The answer is glucose" not in response.content


@pytest.mark.asyncio
async def test_focus_cue_appears_every_4_turns(mock_llm_good):
    engine = SocraticDialogueManager(llm=mock_llm_good)
    history = [
        DialogueTurn(role="student", content=f"message {i}")
        for i in range(4)
    ]
    response = await engine.respond(
        student_id="stu001",
        student_message="And then what?",
        history=history,
        concept_id="ct_loops",
        student_context={
            "student_name": "Rahul",
            "grade": "6",
            "mastery_score": 0.3,
            "concept_name": "Loops",
            "learning_velocity": "moderate",
            "concept_description": "Loops repeat instructions.",
            "simulator_state": "None",
            "language": "English",
            "session_type": "chat",
        },
    )
    assert response.focus_cue is not None
