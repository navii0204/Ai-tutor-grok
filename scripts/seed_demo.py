"""Seed demo data — creates students, sessions, and mastery records for UI showcase."""

from __future__ import annotations

import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from src.core.database import Base
from src.core.student_model.service import StudentModelService
from src.core.student_model.schemas import (
    CreateStudentRequest,
    SessionSummarySchema,
    UpdateMasteryRequest,
)

DB_URL = "sqlite+aiosqlite:///./brainecosystem.db"
TENANT = "demo-school-001"

STUDENTS = [
    {"external_id": "s001", "name": "Arjun Sharma",  "grade": "7", "segment": "school"},
    {"external_id": "s002", "name": "Priya Nair",    "grade": "7", "segment": "school"},
    {"external_id": "s003", "name": "Rahul Gupta",   "grade": "6", "segment": "school"},
    {"external_id": "s004", "name": "Sneha Patel",   "grade": "8", "segment": "school"},
    {"external_id": "s005", "name": "Karan Mehta",   "grade": "7", "segment": "school"},
    {"external_id": "j001", "name": "Diya Iyer",     "grade": "11", "segment": "jee"},
    {"external_id": "j002", "name": "Aryan Singh",   "grade": "11", "segment": "jee"},
]

MASTERY_DATA = [
    # Arjun — strong in science, weaker in math
    ("s001", [
        ("sci_photosynthesis", 0.75, True),
        ("sci_force_motion", 0.55, True),
        ("math_fractions_basic", 0.4, False),
        ("ct_loops", 0.65, True),
    ]),
    # Priya — well-rounded
    ("s002", [
        ("sci_photosynthesis", 0.85, True),
        ("math_fractions_basic", 0.7, True),
        ("math_fractions_operations", 0.5, False),
        ("ct_loops", 0.8, True),
        ("ct_conditionals", 0.45, False),
    ]),
    # Rahul — just starting
    ("s003", [
        ("math_fractions_basic", 0.2, False),
        ("ct_loops", 0.15, False),
    ]),
    # Sneha — advanced
    ("s004", [
        ("sci_photosynthesis", 0.9, True),
        ("sci_force_motion", 0.8, True),
        ("math_fractions_basic", 0.95, True),
        ("math_fractions_operations", 0.75, True),
        ("ct_loops", 0.85, True),
        ("ct_conditionals", 0.7, True),
    ]),
    # Karan — needs support
    ("s005", [
        ("math_fractions_basic", 0.3, False),
        ("sci_photosynthesis", 0.25, False),
    ]),
    # JEE students
    ("j001", [
        ("jee_kinematics_1d", 0.7, True),
        ("jee_kinematics_2d", 0.5, True),
        ("jee_limits", 0.65, True),
    ]),
    ("j002", [
        ("jee_kinematics_1d", 0.45, False),
        ("jee_limits", 0.55, True),
        ("jee_mole_concept", 0.6, True),
    ]),
]


async def seed():
    engine = create_async_engine(DB_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    factory = async_sessionmaker(bind=engine, expire_on_commit=False)

    student_ids: dict[str, str] = {}

    async with factory() as session:
        svc = StudentModelService(session, TENANT)

        # Create students
        for s in STUDENTS:
            profile = await svc.get_or_create_student(
                CreateStudentRequest(
                    external_id=s["external_id"],
                    name=s["name"],
                    grade=s["grade"],
                    segment=s["segment"],
                    tenant_id=TENANT,
                    language="en",
                )
            )
            student_ids[s["external_id"]] = profile.id
            print(f"  ✓ Student: {s['name']} ({profile.id[:8]}…)")

        await session.commit()

    # Add mastery scores
    for ext_id, masteries in MASTERY_DATA:
        db_id = student_ids.get(ext_id)
        if not db_id:
            continue
        async with factory() as session:
            svc = StudentModelService(session, TENANT)
            for concept_id, score, reasoning_ok in masteries:
                await svc.update_concept_mastery(
                    student_id=db_id,
                    tenant_id=TENANT,
                    req=UpdateMasteryRequest(
                        concept_id=concept_id,
                        delta_score=score,
                        reasoning_correct=reasoning_ok,
                    ),
                )
            await session.commit()
        print(f"  ✓ Mastery seeded for {ext_id} ({len(masteries)} concepts)")

    # Add sessions for holistic markers
    for ext_id, _ in MASTERY_DATA:
        db_id = student_ids.get(ext_id)
        if not db_id:
            continue
        import random
        async with factory() as session:
            svc = StudentModelService(session, TENANT)
            record = await svc.open_session(
                student_id=db_id,
                tenant_id=TENANT,
                session_type="chat",
                segment="school" if ext_id.startswith("s") else "jee",
                concept_ids=["sci_photosynthesis"],
            )
            await svc.close_session(
                session_id=record.id,
                student_id=db_id,
                summary=SessionSummarySchema(
                    session_type="chat",
                    reasoning_quality=random.uniform(0.4, 0.9),
                    reflection_depth=random.uniform(0.3, 0.8),
                    focus_signal=random.uniform(0.5, 0.95),
                    duration_seconds=random.randint(600, 2400),
                    concept_ids=["sci_photosynthesis"],
                    ethical_moments=[{"moment": "discussed deforestation impact"}] if random.random() > 0.5 else [],
                    dialogue_summary="Student explored photosynthesis through Socratic questioning.",
                ),
            )
            await session.commit()

    print("\n✅ Demo data seeded successfully!")
    print(f"   {len(STUDENTS)} students · mastery records · session histories")
    print("\n   Demo student IDs to use in API calls:")
    for ext_id, db_id in student_ids.items():
        name = next(s["name"] for s in STUDENTS if s["external_id"] == ext_id)
        print(f"   {name:20s}  →  {db_id}")

    await engine.dispose()


if __name__ == "__main__":
    print("🌱 Seeding BrainEcosystem demo data…\n")
    asyncio.run(seed())
