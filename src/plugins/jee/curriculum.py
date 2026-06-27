"""JEE Curriculum Plugin — conceptual depth for JEE Main/Advanced preparation.

Focus: deep conceptual understanding + multi-step reasoning, NOT rote formulas.
The Socratic engine is especially important here — students must DERIVE, not recall.
"""

from __future__ import annotations

from typing import Any

from src.core.curriculum_mapper.concept_graph import ConceptGraph
from src.core.curriculum_mapper.interfaces import (
    ConceptNode,
    CurriculumPlugin,
    LearningObjective,
)

JEE_CONCEPTS: list[ConceptNode] = [
    # ── Physics ───────────────────────────────────────────────────────────────
    ConceptNode(
        id="jee_kinematics_1d",
        name="1D Kinematics — Motion Along a Line",
        description=(
            "Deep understanding of displacement, velocity, acceleration relationships. "
            "Graphical analysis: v-t and x-t graphs. Equations of motion from first principles."
        ),
        subject="physics",
        grade="11",
        segment="jee",
        prerequisites=[],
        objectives=[
            LearningObjective(
                id="jee_kin_1",
                description="Derive the equations of motion from v = dx/dt without memorisation",
                bloom_level="create",
                nep_competency="mathematical_reasoning",
            ),
            LearningObjective(
                id="jee_kin_2",
                description="Interpret v-t graph: find displacement as area, acceleration as slope",
                bloom_level="analyze",
                nep_competency="scientific_inquiry",
            ),
        ],
        real_world_connections=["Train journey analysis", "Braking distance in cars", "Free fall"],
        india_context_examples=[
            "A Shatabdi Express decelerates from 150 km/h to rest. Derive the stopping distance.",
            "A ball dropped from Qutub Minar (73 m) — predict landing time without a formula, just from v=at.",
        ],
        mastery_keywords=[
            "displacement", "velocity", "acceleration", "uniform motion", "v-t graph",
            "area under curve", "slope", "equation of motion", "integrate"
        ],
        estimated_minutes=45,
        tags=["jee", "physics", "grade11", "kinematics"],
    ),
    ConceptNode(
        id="jee_kinematics_2d",
        name="2D Kinematics — Projectile Motion",
        description=(
            "Projectile as superposition of horizontal uniform motion + vertical free fall. "
            "Range, time of flight, maximum height derivations. Angle of maximum range."
        ),
        subject="physics",
        grade="11",
        segment="jee",
        prerequisites=["jee_kinematics_1d"],
        objectives=[
            LearningObjective(
                id="jee_proj_1",
                description="Derive range formula R = u²sin2θ/g from first principles",
                bloom_level="create",
                nep_competency="mathematical_reasoning",
            )
        ],
        real_world_connections=["Javelin throw", "Artillery shell trajectory", "Basketball arc"],
        india_context_examples=[
            "A cricket ball hit at 45° with 25 m/s — derive where it lands. Don't use the formula directly.",
        ],
        mastery_keywords=["projectile", "range", "time of flight", "maximum height", "component", "parabola"],
        estimated_minutes=50,
        tags=["jee", "physics", "grade11"],
    ),
    ConceptNode(
        id="jee_newton_laws",
        name="Newton's Laws — Deep Understanding",
        description=(
            "All three laws as a coherent system. Free body diagrams. Constraint relations. "
            "Common JEE pitfalls: pseudo-force in non-inertial frames, tension in Atwood machine."
        ),
        subject="physics",
        grade="11",
        segment="jee",
        prerequisites=["jee_kinematics_1d"],
        objectives=[
            LearningObjective(
                id="jee_newt_1",
                description="Draw accurate free-body diagrams for multi-body systems",
                bloom_level="apply",
                nep_competency="analytical_reasoning",
            )
        ],
        real_world_connections=["Lift acceleration", "Car on banked road", "Rocket propulsion"],
        india_context_examples=[
            "In an Otis lift going up at 2 m/s², what does your weighing scale show?",
        ],
        mastery_keywords=["inertia", "free body diagram", "net force", "normal force", "friction", "pseudo force"],
        estimated_minutes=60,
        tags=["jee", "physics", "grade11"],
    ),
    # ── Mathematics ───────────────────────────────────────────────────────────
    ConceptNode(
        id="jee_limits",
        name="Limits — The Foundation of Calculus",
        description=(
            "Intuitive and formal understanding of limits. L'Hôpital's rule. "
            "Standard limits. Indeterminate forms. Sandwich theorem."
        ),
        subject="mathematics",
        grade="11",
        segment="jee",
        prerequisites=[],
        objectives=[
            LearningObjective(
                id="jee_lim_1",
                description="Evaluate limit of sin(x)/x as x→0 without L'Hôpital — geometrically",
                bloom_level="evaluate",
                nep_competency="mathematical_reasoning",
            )
        ],
        india_context_examples=[
            "Zeno's paradox of Achilles and the tortoise — can you resolve it using limits?"
        ],
        mastery_keywords=["limit", "approaches", "indeterminate", "L'Hopital", "continuity", "sandwich theorem"],
        estimated_minutes=50,
        tags=["jee", "mathematics", "grade11", "calculus"],
    ),
    ConceptNode(
        id="jee_derivatives",
        name="Derivatives — Rate of Change",
        description=(
            "Derivative as limit of difference quotient. Chain rule, product rule, quotient rule. "
            "Implicit differentiation. Applications: maxima/minima, tangent lines."
        ),
        subject="mathematics",
        grade="11",
        segment="jee",
        prerequisites=["jee_limits"],
        objectives=[
            LearningObjective(
                id="jee_deriv_1",
                description="Derive d/dx(sin x) from first principles",
                bloom_level="create",
                nep_competency="mathematical_reasoning",
            )
        ],
        india_context_examples=[
            "A Ferris wheel of radius 10m rotates. At what rate is a rider's height changing at the top?"
        ],
        mastery_keywords=["derivative", "rate of change", "chain rule", "product rule", "tangent", "maxima", "minima"],
        estimated_minutes=55,
        tags=["jee", "mathematics", "grade11", "calculus"],
    ),
    # ── Chemistry ─────────────────────────────────────────────────────────────
    ConceptNode(
        id="jee_mole_concept",
        name="Mole Concept — Counting Atoms at Scale",
        description=(
            "Avogadro's number as a counting unit. Molar mass. Mole fractions. "
            "Stoichiometry as a ratio problem, not a formula problem."
        ),
        subject="chemistry",
        grade="11",
        segment="jee",
        prerequisites=[],
        objectives=[
            LearningObjective(
                id="jee_mole_1",
                description="Calculate number of molecules from grams without rote formula",
                bloom_level="apply",
                nep_competency="scientific_reasoning",
            )
        ],
        india_context_examples=[
            "How many water molecules are in a glass of water (250 mL)? Think through it step by step."
        ],
        mastery_keywords=["mole", "Avogadro", "molar mass", "stoichiometry", "limiting reagent"],
        estimated_minutes=40,
        tags=["jee", "chemistry", "grade11"],
    ),
]

JEE_PROJECTS: list[dict[str, Any]] = [
    {
        "id": "jee_proj_motion_analysis",
        "name": "Video Analysis of Real-World Projectile",
        "description": (
            "Record a ball being thrown, use free tools to track position frame by frame, "
            "and verify the parabolic trajectory. Compare with theoretical prediction."
        ),
        "concept_ids": ["jee_kinematics_2d"],
        "grades": ["11", "12"],
        "duration_hours": 4,
        "nep_competencies": ["scientific_inquiry", "data_literacy"],
        "ethical_thread": "Discuss how physics of projectiles is used in weapons technology. What responsibility do scientists have?",
    }
]


class JEECurriculumPlugin(CurriculumPlugin):
    """JEE-focused curriculum plugin emphasising conceptual depth over formula memorisation."""

    def __init__(self) -> None:
        self._graph = ConceptGraph()
        self._graph.add_concepts(JEE_CONCEPTS)

    @property
    def segment_id(self) -> str:
        return "jee"

    @property
    def supported_grades(self) -> list[str]:
        return ["11", "12"]

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
            p for p in JEE_PROJECTS
            if grade in p["grades"] and cid_set.intersection(set(p["concept_ids"]))
        ]
