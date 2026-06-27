"""FocusCueEngine — subtle mind-body alignment nudges woven into learning.

These are NOT meditation sessions; they are brief, natural prompts that help
students transition into focused learning (NEP's holistic development principle).
Cues are chosen based on time of day, focus signal history, and session context.
"""

from __future__ import annotations

import random
from datetime import datetime, timezone

FOCUS_CUES: dict[str, list[str]] = {
    "session_start": [
        "Before we begin — take one slow breath and let go of whatever else is on your mind. Ready?",
        "Let's start fresh. Roll your shoulders back, sit comfortably, and bring your curiosity here.",
        "Imagine your mind is like a clear lake before we toss the first stone of a question. Settled?",
    ],
    "stuck": [
        "When we feel stuck, it often means we're right at the edge of understanding. Take a breath. What do you know for sure?",
        "It's okay not to know yet — that's exactly where real learning lives. Breathe. What's one small thing you could try?",
        "Even the best scientists get stuck. It's a sign your mind is working hard. Pause, and come back to what you do know.",
    ],
    "mid_session": [
        "Quick check-in: how's your energy? Stretch if you need to — your body is part of your thinking.",
        "You've been thinking hard. Notice that. Take a breath, then let's keep going.",
    ],
    "breakthrough": [
        "That moment of understanding — notice how that feels. That's your mind making a new connection.",
        "You just figured something out. That feeling? That's what real learning feels like. Hold on to it.",
    ],
    "reflection": [
        "Before we wrap up — what surprised you most about what you learned today?",
        "Take a moment. What will you remember from this session a week from now?",
        "What's one question this session opened up for you that you'd love to explore?",
    ],
}


class FocusCueEngine:
    def get_cue(self, cue_type: str, student_focus_signal: float = 0.5) -> str:
        cues = FOCUS_CUES.get(cue_type, FOCUS_CUES["mid_session"])
        if student_focus_signal < 0.4 and cue_type == "mid_session":
            cues = FOCUS_CUES["stuck"]
        return random.choice(cues)

    def session_start_cue(self, hour_of_day: int | None = None) -> str:
        if hour_of_day is None:
            hour_of_day = datetime.now(timezone.utc).hour
        # Morning: energising; afternoon: grounding; evening: calming
        if hour_of_day < 12:
            return (
                "Good morning energy! Take one deep breath, sit tall, "
                "and let's bring our full curiosity here. Ready?"
            )
        if hour_of_day < 17:
            return (
                "Afternoon can feel heavy — that's normal. "
                "Stretch your arms up, take a breath, and let's focus together."
            )
        return (
            "Evening learning — your brain is actually good at consolidating knowledge now. "
            "Breathe, relax your jaw, and let's begin."
        )
