"""SocraticDialogueManager — the LLM-powered Socratic tutor.

Builds a rich, context-aware system prompt incorporating:
  - Student holistic profile (mastery, velocity, emotional state)
  - Curriculum concept metadata
  - Session history
  - Active simulator state
  - NEP philosophy and Socratic discipline instructions

The guard layer is always applied before returning a response.
"""

from __future__ import annotations

import asyncio
from typing import Any, AsyncIterator

from src.core.logging_config import get_logger
from src.core.multimodal_context.llm_provider import LLMProvider
from .guards import SocraticGuard
from .interfaces import (
    AdaptiveHint,
    DialogueTurn,
    SocraticEngineInterface,
    SocraticResponse,
)

log = get_logger(__name__)

_SYSTEM_PROMPT_TEMPLATE = """You are BrainGuide — a wise, patient, Socratic learning companion for Indian school students.

CORE PHILOSOPHY:
- You NEVER give the direct answer. Ever. Not even if the student begs.
- You guide through carefully chosen questions that help the student discover answers themselves.
- You celebrate the process of thinking, not just correct answers.
- You connect concepts to real Indian contexts, everyday experiences, and practical examples.
- You notice when a student seems frustrated and gently encourage persistence.
- You occasionally (every 3-4 turns) offer a brief mind-body cue: "Take a breath and notice what you already know."
- You reflect ethical dimensions when they naturally arise in a concept.
- You speak simply and warmly — you are a wise elder, not a textbook.

CURRENT STUDENT CONTEXT:
- Name: {student_name}
- Grade: {grade}
- Mastery of this concept: {mastery_pct}%
- Learning velocity: {velocity}
- Current concept: {concept_name}
- Session type: {session_type}

CONCEPT CONTEXT:
{concept_description}

ACTIVE SIMULATOR STATE (if any):
{simulator_state}

SOCRATIC RULES (NEVER BREAK):
1. End every response with a genuine inquiry question.
2. If you sense the student is close to the answer, ask "What happens if you try that?"
3. If the student gives a wrong answer, reflect it back: "Interesting — what made you think that?"
4. If the student is stuck, offer a hint by analogy, never by formula.
5. For ethical moments, ask "What do you think is the right thing here, and why?"

Respond in {language}. Keep responses under 120 words. Be warm, curious, and delightful."""


class SocraticDialogueManager(SocraticEngineInterface):
    def __init__(self, llm: LLMProvider, guard: SocraticGuard | None = None) -> None:
        self._llm = llm
        self._guard = guard or SocraticGuard()

    async def respond(
        self,
        student_id: str,
        student_message: str,
        history: list[DialogueTurn],
        concept_id: str,
        student_context: dict[str, Any],
    ) -> SocraticResponse:
        system_prompt = self._build_system_prompt(student_context)
        messages = self._history_to_messages(history)
        messages.append({"role": "user", "content": student_message})

        raw = await self._llm.chat(system_prompt=system_prompt, messages=messages)

        guard_result = self._guard.check(raw)
        if not guard_result.passed:
            log.warning(
                "socratic_guard_triggered",
                student_id=student_id,
                reason=guard_result.reason,
            )
            final_text = guard_result.sanitised_text
        else:
            final_text = raw

        mastery_delta, reasoning_correct = self._assess_response(
            student_message, student_context
        )
        focus_cue = self._maybe_focus_cue(len(history))
        reflection_prompt = self._maybe_reflection(student_message, student_context)

        return SocraticResponse(
            content=final_text,
            is_question="?" in final_text,
            hint=None,
            detected_misconception=None,
            focus_cue=focus_cue,
            reflection_prompt=reflection_prompt,
            mastery_delta=mastery_delta,
            reasoning_correct=reasoning_correct,
        )

    async def stream_respond(
        self,
        student_id: str,
        student_message: str,
        history: list[DialogueTurn],
        concept_id: str,
        student_context: dict[str, Any],
    ) -> AsyncIterator[str]:
        """Buffer-then-stream: collect full LLM output, guard it, yield char-by-char.

        CRITICAL SAFETY CONSTRAINT: We MUST buffer the full LLM response before
        streaming any of it to the client. Streaming raw output would let the first
        tokens of a direct answer reach the student before SocraticGuard detects
        the pattern. Buffer first → guard on complete text → re-stream approved text.
        """
        system_prompt = self._build_system_prompt(student_context)
        messages = self._history_to_messages(history)
        messages.append({"role": "user", "content": student_message})

        # Phase 1: Buffer the full response from the LLM stream
        buffer: list[str] = []
        async for chunk in self._llm.stream_chat(system_prompt=system_prompt, messages=messages):
            buffer.append(chunk)
        raw = "".join(buffer)

        # Phase 2: Guard the complete buffered text
        guard_result = self._guard.check(raw)
        if not guard_result.passed:
            log.warning(
                "socratic_guard_triggered",
                student_id=student_id,
                reason=guard_result.reason,
            )
        final_text = guard_result.sanitised_text

        # Phase 3: Re-stream the guard-approved text character by character
        for char in final_text:
            yield char
            await asyncio.sleep(0.008)  # ~125 chars/sec — comfortable reading pace

    async def generate_opening_question(
        self, concept_id: str, student_context: dict[str, Any]
    ) -> str:
        system_prompt = self._build_system_prompt(student_context)
        prompt = (
            f"Generate a single engaging opening question to introduce the concept "
            f"'{student_context.get('concept_name', concept_id)}' to this student. "
            f"Connect to something from daily Indian life. One question only."
        )
        raw = await self._llm.chat(
            system_prompt=system_prompt, messages=[{"role": "user", "content": prompt}]
        )
        guard_result = self._guard.check(raw)
        return guard_result.sanitised_text

    async def detect_misconception(
        self, student_message: str, concept_id: str
    ) -> str | None:
        prompt = (
            f"A student studying '{concept_id}' said: '{student_message}'. "
            f"Identify ONE specific misconception in 10 words or fewer, or reply 'none'."
        )
        result = await self._llm.chat(
            system_prompt="You are a misconception detector. Be precise and brief.",
            messages=[{"role": "user", "content": prompt}],
        )
        return None if "none" in result.lower() else result.strip()

    # ── Private helpers ────────────────────────────────────────────────────────

    def _build_system_prompt(self, ctx: dict[str, Any]) -> str:
        mastery = ctx.get("mastery_score", 0.0)
        return _SYSTEM_PROMPT_TEMPLATE.format(
            student_name=ctx.get("student_name", "Student"),
            grade=ctx.get("grade", "6"),
            mastery_pct=round(mastery * 100),
            velocity=ctx.get("learning_velocity", "moderate"),
            concept_name=ctx.get("concept_name", "the concept"),
            session_type=ctx.get("session_type", "chat"),
            concept_description=ctx.get("concept_description", ""),
            simulator_state=ctx.get("simulator_state", "None"),
            language=ctx.get("language", "English"),
        )

    def _history_to_messages(self, history: list[DialogueTurn]) -> list[dict[str, str]]:
        role_map = {"student": "user", "tutor": "assistant"}
        return [
            {"role": role_map.get(t.role, "user"), "content": t.content}
            for t in history[-10:]  # keep last 10 turns to stay within context limit
        ]

    def _assess_response(
        self, message: str, ctx: dict[str, Any]
    ) -> tuple[float, bool]:
        """Lightweight heuristic scoring — replaced by LLM rubric in analytics."""
        keywords = ctx.get("mastery_keywords", [])
        matched = sum(1 for kw in keywords if kw.lower() in message.lower())
        if matched >= 3:
            return 0.15, True
        if matched >= 1:
            return 0.07, False
        if len(message) > 80:
            return 0.03, False
        return 0.0, False

    def _maybe_focus_cue(self, turn_count: int) -> str | None:
        if turn_count > 0 and turn_count % 4 == 0:
            return (
                "Before we continue — take one slow breath. "
                "Notice what you already understand about this. Ready?"
            )
        return None

    def _maybe_reflection(self, message: str, ctx: dict[str, Any]) -> str | None:
        ethical_triggers = ["fair", "right", "wrong", "should", "why do we", "environment"]
        if any(t in message.lower() for t in ethical_triggers):
            return "What do you think is the ethical dimension here? Who does this affect?"
        return None
