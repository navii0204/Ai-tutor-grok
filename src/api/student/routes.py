"""Student API — chat, simulator, daily plan, and progress endpoints."""

from __future__ import annotations

import json
from typing import Any

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from src.api.dependencies import (
    AnalyticsDep,
    ContextBuilderDep,
    CurriculumDep,
    DBSessionDep,
    DirectorDep,
    SimulatorDep,
    SocraticDep,
    StudentServiceDep,
    SettingsDep,
)
from src.core.multimodal_context.context_builder import SimulatorStateSnapshot
from src.core.simulator.interfaces import SimulatorCommand
from src.core.socratic_adaptive_engine.interfaces import DialogueTurn
from src.core.student_model.schemas import (
    CreateStudentRequest,
    SessionSummarySchema,
    UpdateMasteryRequest,
)

router = APIRouter()


# ── Student Profile ────────────────────────────────────────────────────────────

@router.post("/profile", status_code=status.HTTP_201_CREATED)
async def create_or_get_student(
    req: CreateStudentRequest,
    service: StudentServiceDep,
    settings: SettingsDep,
) -> dict[str, Any]:
    if not req.tenant_id:
        req.tenant_id = settings.default_tenant_id
    student = await service.get_or_create_student(req)
    return {"id": student.id, "name": student.name, "grade": student.grade}


@router.get("/profile/{student_id}")
async def get_student_profile(
    student_id: str,
    service: StudentServiceDep,
) -> dict[str, Any]:
    student = await service.get_student(student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    m = student.holistic_markers
    return {
        "id": student.id,
        "name": student.name,
        "grade": student.grade,
        "segment": student.segment,
        "holistic_markers": {
            "avg_reasoning_quality": m.avg_reasoning_quality if m else 0,
            "avg_reflection_depth": m.avg_reflection_depth if m else 0,
            "avg_focus_signal": m.avg_focus_signal if m else 0,
            "streak_days": m.streak_days if m else 0,
            "total_sessions": m.total_sessions if m else 0,
            "concepts_mastered_count": m.concepts_mastered_count if m else 0,
        } if m else {},
    }


# ── Student List ──────────────────────────────────────────────────────────────

@router.get("/list")
async def list_students(
    service: StudentServiceDep,
    settings: SettingsDep,
    tenant_id: str | None = None,
    limit: int = 100,
) -> dict[str, Any]:
    """List all students for a tenant. Powers the student-picker UI dropdown."""
    resolved_tenant = tenant_id or settings.default_tenant_id
    students = await service.list_students(resolved_tenant, limit=limit)
    return {
        "tenant_id": resolved_tenant,
        "students": [
            {
                "id": s.id,
                "name": s.name,
                "grade": s.grade,
                "segment": s.segment,
                "external_id": s.external_id,
            }
            for s in students
        ],
    }


# ── Daily Plan ────────────────────────────────────────────────────────────────

@router.get("/daily-plan/{student_id}")
async def get_daily_plan(
    student_id: str,
    service: StudentServiceDep,
    director: DirectorDep,
) -> dict[str, Any]:
    student = await service.get_student(student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    due = await service.get_due_review_concepts(student_id)
    goal = director.build_weekly_goal(student, next_concepts=[])
    plan = director.build_daily_plan(student, due_reviews=due, available_concepts=[], weekly_goal=goal)
    return {
        "focus_cue": plan.focus_cue,
        "streak_days": plan.streak_days,
        "motivational_message": plan.motivational_message,
        "reflection_prompt": plan.reflection_prompt,
        "weekly_goal_progress": plan.weekly_goal_progress,
        "activities": [
            {
                "type": a.activity_type,
                "concept_id": a.concept_id,
                "concept_name": a.concept_name,
                "estimated_minutes": a.estimated_minutes,
                "reason": a.reason,
            }
            for a in plan.activities
        ],
    }


# ── Socratic Chat ─────────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    student_id: str
    concept_id: str
    message: str
    history: list[dict[str, str]] = Field(default_factory=list)
    session_id: str | None = None
    simulator_state: dict[str, Any] | None = None


@router.post("/chat")
async def socratic_chat(
    req: ChatRequest,
    service: StudentServiceDep,
    engine: SocraticDep,
    curriculum: CurriculumDep,
    context_builder: ContextBuilderDep,
) -> dict[str, Any]:
    student = await service.get_student(req.student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    segment = student.segment
    plugin = curriculum.get(segment)
    concept = plugin.get_concept(req.concept_id)
    if not concept:
        raise HTTPException(status_code=404, detail=f"Concept '{req.concept_id}' not found")

    mastery_entry = next(
        (cm for cm in (student.concept_masteries or []) if cm.concept_id == req.concept_id),
        None,
    )
    mastery_score = mastery_entry.mastery_score if mastery_entry else 0.0
    confidence = mastery_entry.confidence if mastery_entry else 0.5

    sim_snapshot = None
    if req.simulator_state:
        sim_snapshot = SimulatorStateSnapshot(
            simulator_id=req.simulator_state.get("simulator_id", "unknown"),
            state_description=req.simulator_state.get("description", ""),
            raw_state=req.simulator_state,
        )

    ctx = context_builder.build(
        student=student,
        concept=concept,
        mastery_score=mastery_score,
        confidence=confidence,
        session_type="chat",
        simulator_snapshot=sim_snapshot,
    )

    history = [
        DialogueTurn(role=t["role"], content=t["content"]) for t in req.history
    ]

    response = await engine.respond(
        student_id=req.student_id,
        student_message=req.message,
        history=history,
        concept_id=req.concept_id,
        student_context=ctx.to_llm_dict(),
    )

    # Update mastery based on response quality
    if response.mastery_delta != 0:
        await service.update_concept_mastery(
            student_id=req.student_id,
            tenant_id=student.tenant_id,
            req=UpdateMasteryRequest(
                concept_id=req.concept_id,
                delta_score=response.mastery_delta,
                reasoning_correct=response.reasoning_correct,
                session_id=req.session_id,
            ),
            segment=segment,
        )

    return {
        "response": response.content,
        "is_question": response.is_question,
        "focus_cue": response.focus_cue,
        "reflection_prompt": response.reflection_prompt,
        "mastery_delta": response.mastery_delta,
    }


# ── Streaming Chat ────────────────────────────────────────────────────────────

@router.post("/chat/stream")
async def socratic_chat_stream(
    req: ChatRequest,
    service: StudentServiceDep,
    engine: SocraticDep,
    curriculum: CurriculumDep,
    context_builder: ContextBuilderDep,
) -> StreamingResponse:
    """SSE streaming version of /chat. Yields guard-approved text char by char.

    Uses buffer-then-stream: full LLM response is collected, SocraticGuard is
    applied to the complete text, then the approved response streams to the client.
    Mastery update is NOT performed here — use /chat for that side effect.
    """
    student = await service.get_student(req.student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    segment = student.segment
    plugin = curriculum.get(segment)
    concept = plugin.get_concept(req.concept_id)
    if not concept:
        raise HTTPException(status_code=404, detail=f"Concept '{req.concept_id}' not found")

    mastery_entry = next(
        (cm for cm in (student.concept_masteries or []) if cm.concept_id == req.concept_id),
        None,
    )
    mastery_score = mastery_entry.mastery_score if mastery_entry else 0.0
    confidence = mastery_entry.confidence if mastery_entry else 0.5

    sim_snapshot = None
    if req.simulator_state:
        sim_snapshot = SimulatorStateSnapshot(
            simulator_id=req.simulator_state.get("simulator_id", "unknown"),
            state_description=req.simulator_state.get("description", ""),
            raw_state=req.simulator_state,
        )

    ctx = context_builder.build(
        student=student,
        concept=concept,
        mastery_score=mastery_score,
        confidence=confidence,
        session_type="chat",
        simulator_snapshot=sim_snapshot,
    )

    history = [
        DialogueTurn(role=t["role"], content=t["content"]) for t in req.history
    ]

    async def event_stream():
        async for char in engine.stream_respond(
            student_id=req.student_id,
            student_message=req.message,
            history=history,
            concept_id=req.concept_id,
            student_context=ctx.to_llm_dict(),
        ):
            yield f"data: {json.dumps({'char': char})}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


# ── Simulator ─────────────────────────────────────────────────────────────────

class SimulatorCommandRequest(BaseModel):
    student_id: str
    simulator_id: str
    command: str
    params: dict[str, Any] = Field(default_factory=dict)
    config: dict[str, Any] | None = None


@router.post("/simulator/command")
async def simulator_command(
    req: SimulatorCommandRequest,
    sim_registry: SimulatorDep,
) -> dict[str, Any]:
    try:
        sim = sim_registry.get(req.simulator_id)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Simulator '{req.simulator_id}' not found")

    if req.command == "reset":
        state = sim.reset(req.config)
        return {"success": True, "message": "Reset", "state": state.entity_states}

    cmd = SimulatorCommand(command=req.command, params=req.params)
    result = sim.execute_command(cmd)
    return {
        "success": result.success,
        "message": result.message,
        "state": result.new_state.entity_states,
        "sensors": [
            {"id": s.sensor_id, "value": s.value, "unit": s.unit}
            for s in result.new_state.sensor_readings
        ],
        "events": result.new_state.event_log,
        "is_complete": result.new_state.is_complete,
        "score": result.new_state.score,
    }


@router.get("/simulator/{simulator_id}/commands")
async def list_simulator_commands(
    simulator_id: str, sim_registry: SimulatorDep
) -> dict[str, Any]:
    try:
        sim = sim_registry.get(simulator_id)
        return {"commands": sim.list_commands()}
    except KeyError:
        raise HTTPException(status_code=404, detail="Simulator not found")


# ── Session Management ────────────────────────────────────────────────────────

class OpenSessionRequest(BaseModel):
    student_id: str
    session_type: str = "chat"
    concept_ids: list[str] = Field(default_factory=list)


@router.post("/session/open")
async def open_session(
    req: OpenSessionRequest,
    service: StudentServiceDep,
    settings: SettingsDep,
) -> dict[str, Any]:
    student = await service.get_student(req.student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    record = await service.open_session(
        student_id=req.student_id,
        tenant_id=student.tenant_id,
        session_type=req.session_type,
        segment=student.segment,
        concept_ids=req.concept_ids,
    )
    return {"session_id": record.id, "started_at": record.started_at.isoformat()}


@router.post("/session/{session_id}/close")
async def close_session(
    session_id: str,
    summary: SessionSummarySchema,
    student_id: str,
    service: StudentServiceDep,
) -> dict[str, Any]:
    record = await service.close_session(session_id, student_id, summary)
    if not record:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"closed": True, "session_id": session_id}
