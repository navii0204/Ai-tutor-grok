"""MockLLMProvider — local fallback when Ollama is unavailable.

Produces realistic Socratic responses so the full UI is demonstrable
without a running LLM. Activated via LLM_PROVIDER=mock in .env.
"""

from __future__ import annotations

import random
from typing import Any

from .llm_provider import LLMProvider

_SOCRATIC_RESPONSES = [
    "That's a thoughtful start! What makes you think that? Can you trace where that idea comes from?",
    "Interesting — you're on to something. What would happen if you changed just one thing in that scenario? What do you notice?",
    "I like how you're thinking! Before we go further, what do you already know that might be connected to this? What comes to mind?",
    "Good observation! Now here's a nudge — can you think of a situation from daily life where you've seen something similar? What was it?",
    "You're getting closer! What's the difference between what you said and the full picture? What might be missing?",
    "Excellent reasoning so far. If a friend asked you to explain this in one sentence, what would you say? Try it!",
    "Hmm, let's slow down here. What happens step by step if we trace this from the very beginning? Walk me through it.",
    "Great question! Before I respond — what do YOU think the answer might be? Even a guess helps us think together.",
    "You've noticed something real there. Can you think of a counter-example — a situation where that might NOT be true?",
    "That's the right direction. Now — why does that happen? What's the underlying reason, not just the observation?",
]

_OPENING_QUESTIONS: dict[str, str] = {
    "sci_photosynthesis": (
        "Imagine you grow two identical plants — one in your sunny window, one in a dark cupboard. "
        "What do you predict happens after a week, and more importantly — WHY do you think that would happen?"
    ),
    "math_fractions_basic": (
        "If you share a roti equally among 3 friends and you take one piece — "
        "how would you write that as a number? What does that number mean to you?"
    ),
    "ct_loops": (
        "Imagine you have to tell a robot to walk 5 steps forward. "
        "You could write 'move forward' five times — but is there a smarter way? What pattern do you see?"
    ),
    "ct_conditionals": (
        "A traffic light tells cars when to stop and go. "
        "If you were programming that traffic light, how would you describe its decision in plain English?"
    ),
    "sci_force_motion": (
        "When you kick a cricket ball and it slows down and stops — "
        "what do you think is causing it to slow down? Is something pushing it backwards?"
    ),
    "jee_kinematics_1d": (
        "Without using any formula — if a car starts from rest and reaches 60 km/h in 10 seconds, "
        "what can you tell me about what's happening to its speed each second? What's the pattern?"
    ),
    "jee_limits": (
        "Imagine you keep halving the distance to a wall — 1m, 0.5m, 0.25m... "
        "Will you ever actually reach the wall? What does that tell you about the concept of a 'limit'?"
    ),
}

_LESSON_PLAN_TEMPLATE = """{{
  "warm_up": "Begin with a 3-minute mind-body warm-up: students close eyes, take 3 slow breaths, then visualise where they've seen '{concept}' in real life.",
  "inquiry_questions": [
    "What do you already know or think you know about {concept}?",
    "Can you think of a place in your daily life where this happens?",
    "What would happen if {concept} suddenly stopped working in the world?",
    "How would you explain this to a younger student using only objects in this room?"
  ],
  "activities": [
    {{
      "name": "Pair Exploration",
      "duration": "10 minutes",
      "description": "Students discuss their prior knowledge in pairs. Teacher circulates and listens for misconceptions."
    }},
    {{
      "name": "Guided Inquiry Demo",
      "duration": "15 minutes",
      "description": "Teacher presents a real-world example connected to Indian context. Students predict outcomes before seeing results."
    }},
    {{
      "name": "Socratic Questioning Round",
      "duration": "10 minutes",
      "description": "Full class dialogue. Teacher only asks questions — never explains. Students build understanding together."
    }}
  ],
  "ethical_discussion": "Ask students: If this knowledge could be used in two ways — one helpful, one harmful — who should decide how it's used?",
  "reflection_prompt": "Before we close — write one sentence: What is one thing you understood today that you didn't understand at the start?",
  "assessment_ideas": [
    "Ask students to explain the concept in their own words (no textbook language)",
    "Give a novel scenario and ask them to predict what will happen using the concept",
    "Peer teaching: each student explains to one partner"
  ]
}}"""


class MockLLMProvider(LLMProvider):
    """Drop-in mock for development/demo without a running Ollama instance."""

    async def chat(
        self,
        system_prompt: str,
        messages: list[dict[str, str]],
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> str:
        last_user = next(
            (m["content"] for m in reversed(messages) if m["role"] == "user"), ""
        )

        # Lesson plan request
        if "lesson plan" in system_prompt.lower() or "lesson plan" in last_user.lower():
            concept = "this concept"
            for line in last_user.split("\n"):
                if line.startswith("Concept:"):
                    concept = line.replace("Concept:", "").strip()
                    break
            return _LESSON_PLAN_TEMPLATE.replace("{concept}", concept)

        # Rubric request
        if "rubric" in last_user.lower():
            return (
                '{"dimensions": ['
                '{"name": "Conceptual Understanding", "levels": {"Beginning": "Cannot explain in own words", "Developing": "Partial explanation with some accuracy", "Proficient": "Clear, accurate explanation with examples"}},'
                '{"name": "Reasoning Quality", "levels": {"Beginning": "States facts only", "Developing": "Shows some cause-effect thinking", "Proficient": "Explains WHY with logical steps"}},'
                '{"name": "Application", "levels": {"Beginning": "Cannot apply to new situation", "Developing": "Applies with guidance", "Proficient": "Transfers independently to novel problems"}},'
                '{"name": "Reflection", "levels": {"Beginning": "No self-awareness of learning", "Developing": "Identifies one thing learned", "Proficient": "Identifies understanding AND remaining questions"}}'
                "]}"
            )

        # Parent report request
        if "parent report" in last_user.lower() or "write a parent report" in last_user.lower():
            return (
                "This week, your child explored some truly fascinating ideas in science and mathematics. "
                "They showed real curiosity, asking questions that went beyond what was expected. "
                "One moment stood out: when asked why plants need sunlight, they paused and said "
                "'Is it because they need energy, like we need food?' — that kind of thinking shows deep understanding. "
                "They also showed wonderful persistence when they found something difficult, trying again without giving up. "
                "At home, you could try this: ask them to explain one thing they learned this week as if teaching you. "
                "You'll be amazed at what they know! Keep encouraging their curiosity — it's their greatest strength."
            )

        # Misconception detection
        if "misconception" in last_user.lower():
            return "none"

        # Opening question for known concepts
        concept_id = ""
        for line in system_prompt.split("\n"):
            if "concept_id" in line.lower() or "current concept:" in line.lower():
                concept_id = line.split(":")[-1].strip()
                break
        if concept_id in _OPENING_QUESTIONS:
            return _OPENING_QUESTIONS[concept_id]

        # Check opening question pattern
        for cid, q in _OPENING_QUESTIONS.items():
            if cid.replace("_", " ") in last_user.lower() or cid in last_user:
                return q

        return random.choice(_SOCRATIC_RESPONSES)

    async def embed(self, text: str) -> list[float]:
        import hashlib
        h = hashlib.md5(text.encode()).digest()
        return [b / 255.0 for b in h[:8]] + [0.0] * 760

    async def health_check(self) -> bool:
        return True

    async def aclose(self) -> None:
        pass
