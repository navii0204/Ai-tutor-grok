"""School Curriculum Plugin — NEP-aligned multidisciplinary curriculum for Grades 6–8.

Covers core NCERT-aligned concepts with India context, ethical dimensions,
and project-based learning suggestions. Extend by adding to CONCEPT_CATALOG.
"""

from __future__ import annotations

from typing import Any

from src.core.curriculum_mapper.concept_graph import ConceptGraph
from src.core.curriculum_mapper.interfaces import (
    ConceptNode,
    CurriculumPlugin,
    LearningObjective,
)

CONCEPT_CATALOG: list[ConceptNode] = [
    # ── Mathematics ───────────────────────────────────────────────────────────
    ConceptNode(
        id="math_fractions_basic",
        name="Fractions — What They Mean",
        description="Understanding fractions as parts of a whole, with number line and area models.",
        subject="mathematics",
        grade="6",
        segment="school",
        prerequisites=[],
        objectives=[
            LearningObjective(
                id="obj_frac_1",
                description="Represent a fraction on a number line",
                bloom_level="understand",
                nep_competency="mathematical_reasoning",
            )
        ],
        real_world_connections=["Splitting a pizza", "Measuring ingredients in cooking", "Cricket scoring fractions"],
        india_context_examples=[
            "If a dosa is cut into 4 equal pieces and you eat 1, what fraction did you eat?",
            "A train journey of 360 km — what fraction is 90 km?",
        ],
        mastery_keywords=["numerator", "denominator", "equal parts", "number line", "fraction of a whole"],
        ethical_scenarios=[],
        estimated_minutes=20,
        tags=["ncert", "grade6", "mathematics"],
    ),
    ConceptNode(
        id="math_fractions_operations",
        name="Adding and Subtracting Fractions",
        description="Adding and subtracting fractions with same and different denominators using LCM.",
        subject="mathematics",
        grade="6",
        segment="school",
        prerequisites=["math_fractions_basic"],
        objectives=[
            LearningObjective(
                id="obj_frac_ops_1",
                description="Add fractions with unlike denominators using LCM",
                bloom_level="apply",
                nep_competency="mathematical_reasoning",
            )
        ],
        real_world_connections=["Combining different-sized parcels", "Water in vessels of different capacities"],
        india_context_examples=[
            "Raju drank 1/3 litre of water and Priya drank 1/4 litre. How much did they drink together?",
        ],
        mastery_keywords=["LCM", "common denominator", "equivalent fraction", "simplify"],
        ethical_scenarios=[
            "If there are limited resources (like water in a drought), how should we decide who gets what fraction?"
        ],
        estimated_minutes=25,
        tags=["ncert", "grade6", "mathematics"],
    ),
    ConceptNode(
        id="math_integers",
        name="Integers — Positive and Negative Numbers",
        description="Understanding integers, their placement on a number line, and basic operations.",
        subject="mathematics",
        grade="6",
        segment="school",
        prerequisites=["math_fractions_basic"],
        objectives=[
            LearningObjective(
                id="obj_int_1",
                description="Compare and order integers on a number line",
                bloom_level="understand",
                nep_competency="mathematical_reasoning",
            )
        ],
        real_world_connections=["Temperature below zero", "Below sea level", "Bank balance (credit/debit)"],
        india_context_examples=[
            "Shimla temperature in January can be -5°C. What does that mean?",
            "If you owe someone ₹50, your 'money balance' is -50. How do you represent that?",
        ],
        mastery_keywords=["negative number", "positive number", "number line", "absolute value", "opposite"],
        ethical_scenarios=[],
        estimated_minutes=20,
        tags=["ncert", "grade6", "mathematics"],
    ),
    # ── Science ───────────────────────────────────────────────────────────────
    ConceptNode(
        id="sci_photosynthesis",
        name="Photosynthesis — How Plants Make Food",
        description="Plants as food factories: sunlight + CO2 + water → glucose + oxygen.",
        subject="science",
        grade="7",
        segment="school",
        prerequisites=[],
        objectives=[
            LearningObjective(
                id="obj_photo_1",
                description="Explain the inputs and outputs of photosynthesis",
                bloom_level="understand",
                nep_competency="scientific_inquiry",
            ),
            LearningObjective(
                id="obj_photo_2",
                description="Predict what happens if one input is removed",
                bloom_level="analyze",
                nep_competency="critical_thinking",
            ),
        ],
        real_world_connections=["Crop yields", "Deforestation impact", "Indoor plants improving air"],
        india_context_examples=[
            "Why do farmers in Punjab grow wheat in Rabi season (winter sunlight)?",
            "Why did the Chipko movement protect trees? What happens to local food chains without them?",
        ],
        mastery_keywords=["chlorophyll", "chloroplast", "glucose", "carbon dioxide", "oxygen", "sunlight"],
        ethical_scenarios=[
            "A factory wants to cut down a forest to build a road. What values should guide that decision?"
        ],
        estimated_minutes=25,
        tags=["ncert", "grade7", "science", "biology"],
    ),
    ConceptNode(
        id="sci_force_motion",
        name="Force and Motion — Pushes, Pulls, and Movement",
        description="Forces cause acceleration; balanced vs. unbalanced forces; Newton's first law intuition.",
        subject="science",
        grade="8",
        segment="school",
        prerequisites=[],
        objectives=[
            LearningObjective(
                id="obj_force_1",
                description="Identify balanced and unbalanced forces in everyday situations",
                bloom_level="apply",
                nep_competency="scientific_inquiry",
            )
        ],
        real_world_connections=["Cricket ball trajectory", "Auto-rickshaw braking", "Kite flying"],
        india_context_examples=[
            "When a cricket ball is bowled, what forces act on it?",
            "Why does a loaded truck take longer to stop than an empty one?",
        ],
        mastery_keywords=["force", "balanced", "unbalanced", "inertia", "acceleration", "friction"],
        ethical_scenarios=[],
        estimated_minutes=20,
        tags=["ncert", "grade8", "science", "physics"],
    ),
    # ── Computational Thinking ────────────────────────────────────────────────
    ConceptNode(
        id="ct_loops",
        name="Loops — Doing Things Repeatedly",
        description="Understanding loops (for/while) as a way to avoid repeating instructions.",
        subject="computational_thinking",
        grade="6",
        segment="school",
        prerequisites=[],
        objectives=[
            LearningObjective(
                id="obj_loop_1",
                description="Write a loop to move a robot to a target position",
                bloom_level="apply",
                nep_competency="computational_thinking",
            )
        ],
        real_world_connections=["Assembly lines", "Washing machine cycles", "Daily routine repetition"],
        india_context_examples=[
            "Imagine Ramu has to draw 5 circles. Instead of drawing one by one, what pattern can he use?",
        ],
        mastery_keywords=["iteration", "repeat", "loop", "condition", "counter", "for loop", "while loop"],
        ethical_scenarios=[],
        estimated_minutes=20,
        tags=["computational_thinking", "grade6", "robotics"],
    ),
    ConceptNode(
        id="ct_conditionals",
        name="Conditionals — Making Decisions in Code",
        description="If-else logic: teaching a program (or robot) to make decisions.",
        subject="computational_thinking",
        grade="7",
        segment="school",
        prerequisites=["ct_loops"],
        objectives=[
            LearningObjective(
                id="obj_cond_1",
                description="Write an if-else block to handle two different robot scenarios",
                bloom_level="apply",
                nep_competency="computational_thinking",
            )
        ],
        real_world_connections=["Traffic lights", "ATM logic", "Emergency alert systems"],
        india_context_examples=[
            "How does a smart irrigation system decide when to water crops?",
        ],
        mastery_keywords=["condition", "if", "else", "boolean", "true", "false", "decision"],
        ethical_scenarios=[
            "If an autonomous vehicle has to choose between two bad outcomes, how should it decide? Who should program that choice?"
        ],
        estimated_minutes=20,
        tags=["computational_thinking", "grade7", "robotics"],
    ),
]

PROJECT_SUGGESTIONS: list[dict[str, Any]] = [
    {
        "id": "proj_robot_maze",
        "name": "Robot Maze Navigator",
        "description": "Design a program to navigate the robot through a maze using loops and conditionals.",
        "concept_ids": ["ct_loops", "ct_conditionals"],
        "grades": ["6", "7", "8"],
        "duration_hours": 3,
        "nep_competencies": ["computational_thinking", "problem_solving", "collaboration"],
        "ethical_thread": "Should robots be programmed to prioritise speed or safety?",
    },
    {
        "id": "proj_plant_experiment",
        "name": "Light and Photosynthesis Experiment",
        "description": "Design an experiment: grow two sets of plants with different light conditions and measure growth.",
        "concept_ids": ["sci_photosynthesis"],
        "grades": ["7"],
        "duration_hours": 5,
        "nep_competencies": ["scientific_inquiry", "data_literacy", "critical_thinking"],
        "ethical_thread": "How do farming practices affect both food security and the environment?",
    },
    {
        "id": "proj_force_bridge",
        "name": "Bridge Load Testing",
        "description": "Build a bridge from newspaper/cardboard and test how forces affect its structure.",
        "concept_ids": ["sci_force_motion"],
        "grades": ["8"],
        "duration_hours": 4,
        "nep_competencies": ["engineering_thinking", "scientific_inquiry"],
        "ethical_thread": "How do engineers balance cost and safety when designing public infrastructure?",
    },
]


class SchoolCurriculumPlugin(CurriculumPlugin):
    """NEP-aligned school curriculum plugin for Grades 6–8."""

    def __init__(self) -> None:
        self._graph = ConceptGraph()
        self._graph.add_concepts(CONCEPT_CATALOG)

    @property
    def segment_id(self) -> str:
        return "school"

    @property
    def supported_grades(self) -> list[str]:
        return ["6", "7", "8"]

    def get_concept(self, concept_id: str) -> ConceptNode | None:
        return self._graph.get_concept(concept_id)

    def list_concepts(self, grade: str, subject: str | None = None) -> list[ConceptNode]:
        return self._graph.list_concepts_for_grade(grade, subject)

    def get_prerequisites(self, concept_id: str) -> list[str]:
        return self._graph.get_prerequisites(concept_id)

    def get_next_concepts(self, concept_id: str, mastered: set[str]) -> list[str]:
        return self._graph.get_next_concepts(concept_id, mastered)

    def get_project_suggestions(
        self, concept_ids: list[str], grade: str
    ) -> list[dict[str, Any]]:
        cid_set = set(concept_ids)
        return [
            p for p in PROJECT_SUGGESTIONS
            if grade in p["grades"] and cid_set.intersection(set(p["concept_ids"]))
        ]
