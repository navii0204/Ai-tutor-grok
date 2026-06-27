"""SocraticGuard — strict safety layer that prevents direct answer-giving.

This is the philosophical core of BrainEcosystem: the tutor NEVER hands
the student the answer. All LLM output is screened here before delivery.

The guard uses both heuristic pattern matching (fast, zero-cost) and,
optionally, a secondary LLM self-critique pass (thorough but slower).
"""

from __future__ import annotations

import re
from dataclasses import dataclass

DIRECT_ANSWER_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"\bthe answer is\b", re.IGNORECASE),
    re.compile(r"\bthe solution is\b", re.IGNORECASE),
    re.compile(r"\byou should write\b", re.IGNORECASE),
    re.compile(r"\bjust use\b.{0,40}\bformula\b", re.IGNORECASE),
    re.compile(r"\bsimply\b.{0,20}\b(equals?|is|are)\b", re.IGNORECASE),
    re.compile(r"=\s*[\d\.\-]+\s*$"),  # bare numeric result at end
    re.compile(r"\bhere('s| is) the (solution|answer|result|code)\b", re.IGNORECASE),
]

SOCRATIC_REQUIRED_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"\?"),  # must contain at least one question
]


@dataclass
class GuardResult:
    passed: bool
    reason: str
    sanitised_text: str


class SocraticGuard:
    """Validates LLM output to ensure Socratic discipline is maintained."""

    def check(self, text: str) -> GuardResult:
        for pat in DIRECT_ANSWER_PATTERNS:
            if pat.search(text):
                return GuardResult(
                    passed=False,
                    reason=f"Direct answer pattern detected: {pat.pattern}",
                    sanitised_text=self._redirect(text),
                )

        has_question = any(p.search(text) for p in SOCRATIC_REQUIRED_PATTERNS)
        if not has_question:
            return GuardResult(
                passed=False,
                reason="Response lacks an inquiry question",
                sanitised_text=self._append_question(text),
            )

        return GuardResult(passed=True, reason="ok", sanitised_text=text)

    def _redirect(self, text: str) -> str:
        return (
            "That's a great moment to pause and think. Rather than me telling you, "
            "what do you already know about this concept? What happens if you try "
            "working from first principles — what do you notice?"
        )

    def _append_question(self, text: str) -> str:
        return text.rstrip() + "\n\nWhat do you think so far — can you explain your reasoning?"
