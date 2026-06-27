"""PersonalizationDirector — time-aware learning orchestrator.

Produces daily/weekly adaptive plans that consider:
  - Spaced repetition due items
  - Concept mastery gaps
  - Holistic markers (focus, reflection, resilience)
  - NEP project-based learning cycles
  - Student goals and streak data
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from typing import Any

from src.core.logging_config import get_logger
from src.core.student_model.models import ConceptMastery, HolisticMarkers, StudentProfile
from .focus_cues import FocusCueEngine

log = get_logger(__name__)


@dataclass
class LearningActivity:
    activity_type: str          # "socratic_chat" | "simulator" | "review" | "project" | "reflection"
    concept_id: str
    concept_name: str
    estimated_minutes: int
    priority: float
    reason: str
    opening_cue: str = ""


@dataclass
class DailyPlan:
    student_id: str
    plan_date: date
    focus_cue: str
    activities: list[LearningActivity]
    weekly_goal_progress: float      # 0.0–1.0
    streak_days: int
    motivational_message: str
    reflection_prompt: str


@dataclass
class WeeklyGoal:
    week_start: date
    target_concept_ids: list[str]
    project_suggestion: str | None
    mastery_targets: dict[str, float]  # concept_id → target score
    holistic_focus: str                # "reasoning" | "reflection" | "collaboration"


_MOTIVATIONAL_MESSAGES = [
    "Every question you ask is a step forward. Keep going!",
    "Real understanding takes time — you're building something lasting today.",
    "The best thinkers in the world got there by being curious, just like you.",
    "Struggle is the feeling of your brain growing. Lean into it!",
    "You don't have to know the answer yet — you just have to keep asking.",
    "A Ratan Tata, a Dr. APJ Abdul Kalam — they all started by asking 'why?'",
]

_REFLECTION_PROMPTS = [
    "What's one thing you understood today that you didn't understand yesterday?",
    "If you had to explain today's topic to your younger sibling, how would you start?",
    "What's still confusing? That confusion is your next learning adventure.",
    "What real-world problem could what you learned today help solve?",
    "Did anything surprise you? Why do you think it surprised you?",
]


class PersonalizationDirector:
    def __init__(self, focus_engine: FocusCueEngine | None = None) -> None:
        self._focus_engine = focus_engine or FocusCueEngine()

    def build_daily_plan(
        self,
        student: StudentProfile,
        due_reviews: list[ConceptMastery],
        available_concepts: list[dict[str, Any]],
        weekly_goal: WeeklyGoal | None,
    ) -> DailyPlan:
        markers = student.holistic_markers
        now = datetime.now(timezone.utc)
        focus_cue = self._focus_engine.session_start_cue(now.hour)

        activities: list[LearningActivity] = []

        # 1. Spaced repetition reviews first
        for cm in due_reviews[:2]:
            activities.append(
                LearningActivity(
                    activity_type="review",
                    concept_id=cm.concept_id,
                    concept_name=cm.concept_id.replace("_", " ").title(),
                    estimated_minutes=10,
                    priority=0.95,
                    reason=f"Due for spaced review (mastery: {cm.mastery_score:.0%})",
                    opening_cue=self._focus_engine.get_cue("session_start"),
                )
            )

        # 2. Weak concepts from weekly goal
        if weekly_goal:
            for cid, target in weekly_goal.mastery_targets.items():
                current = next(
                    (c.mastery_score for c in (student.concept_masteries or []) if c.concept_id == cid),
                    0.0,
                )
                if current < target:
                    activities.append(
                        LearningActivity(
                            activity_type="socratic_chat",
                            concept_id=cid,
                            concept_name=cid.replace("_", " ").title(),
                            estimated_minutes=20,
                            priority=0.85,
                            reason=f"Weekly goal: reach {target:.0%} mastery",
                        )
                    )

        # 3. Project or simulator session if holistic markers indicate readiness
        if markers and markers.avg_focus_signal > 0.5 and len(activities) < 3:
            if weekly_goal and weekly_goal.project_suggestion:
                activities.append(
                    LearningActivity(
                        activity_type="simulator",
                        concept_id="project",
                        concept_name=weekly_goal.project_suggestion,
                        estimated_minutes=25,
                        priority=0.7,
                        reason="Project-based learning session",
                    )
                )

        # 4. Reflection activity at end
        activities.append(
            LearningActivity(
                activity_type="reflection",
                concept_id="reflection",
                concept_name="Daily Reflection",
                estimated_minutes=5,
                priority=0.5,
                reason="Consolidate today's learning",
                opening_cue=self._focus_engine.get_cue("reflection"),
            )
        )

        import random
        weekly_progress = self._compute_weekly_progress(student, weekly_goal)

        return DailyPlan(
            student_id=student.id,
            plan_date=now.date(),
            focus_cue=focus_cue,
            activities=sorted(activities, key=lambda a: -a.priority),
            weekly_goal_progress=weekly_progress,
            streak_days=markers.streak_days if markers else 0,
            motivational_message=random.choice(_MOTIVATIONAL_MESSAGES),
            reflection_prompt=random.choice(_REFLECTION_PROMPTS),
        )

    def build_weekly_goal(
        self,
        student: StudentProfile,
        next_concepts: list[str],
        segment: str = "school",
    ) -> WeeklyGoal:
        from datetime import timedelta
        today = date.today()
        week_start = today - timedelta(days=today.weekday())

        mastery_map = {
            cm.concept_id: cm.mastery_score
            for cm in (student.concept_masteries or [])
        }
        targets = {
            cid: min(1.0, mastery_map.get(cid, 0.0) + 0.25)
            for cid in next_concepts[:3]
        }

        markers = student.holistic_markers
        if markers and markers.avg_reflection_depth < 0.4:
            holistic_focus = "reflection"
        elif markers and markers.avg_reasoning_quality < 0.5:
            holistic_focus = "reasoning"
        else:
            holistic_focus = "collaboration"

        return WeeklyGoal(
            week_start=week_start,
            target_concept_ids=next_concepts[:3],
            project_suggestion=None,
            mastery_targets=targets,
            holistic_focus=holistic_focus,
        )

    def _compute_weekly_progress(
        self, student: StudentProfile, goal: WeeklyGoal | None
    ) -> float:
        if not goal:
            return 0.0
        mastery_map = {
            cm.concept_id: cm.mastery_score
            for cm in (student.concept_masteries or [])
        }
        hits = sum(
            1 for cid, target in goal.mastery_targets.items()
            if mastery_map.get(cid, 0.0) >= target
        )
        total = len(goal.mastery_targets) or 1
        return hits / total
