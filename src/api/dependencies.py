"""FastAPI dependency injection — provides shared services to route handlers.

Scalability note: LLMProvider is created once at startup (lifespan) and reused
across requests via app.state to avoid re-initialising the HTTP client.
"""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.analytics_evaluation.evaluator import AnalyticsEvaluator
from src.core.config import Settings, get_settings
from src.core.curriculum_mapper.registry import CurriculumRegistry
from src.core.database import get_db_session
from src.core.multimodal_context.context_builder import ContextBuilder
from src.core.multimodal_context.llm_provider import LLMProvider
from src.core.personalization_director.director import PersonalizationDirector
from src.core.simulator.registry import SimulatorRegistry
from src.core.socratic_adaptive_engine.dialogue_manager import SocraticDialogueManager
from src.core.socratic_adaptive_engine.guards import SocraticGuard
from src.core.student_model.service import StudentModelService

SettingsDep = Annotated[Settings, Depends(get_settings)]
DBSessionDep = Annotated[AsyncSession, Depends(get_db_session)]


def get_llm(request: Request) -> LLMProvider:
    return request.app.state.llm  # type: ignore[return-value]


def get_curriculum_registry(request: Request) -> CurriculumRegistry:
    return request.app.state.curriculum_registry


def get_simulator_registry(request: Request) -> SimulatorRegistry:
    return request.app.state.simulator_registry


LLMDep = Annotated[LLMProvider, Depends(get_llm)]
CurriculumDep = Annotated[CurriculumRegistry, Depends(get_curriculum_registry)]
SimulatorDep = Annotated[SimulatorRegistry, Depends(get_simulator_registry)]


def get_student_service(
    db: DBSessionDep,
    settings: SettingsDep,
) -> StudentModelService:
    return StudentModelService(db, settings.default_tenant_id)


StudentServiceDep = Annotated[StudentModelService, Depends(get_student_service)]


def get_socratic_engine(llm: LLMDep) -> SocraticDialogueManager:
    return SocraticDialogueManager(llm=llm, guard=SocraticGuard())


SocraticDep = Annotated[SocraticDialogueManager, Depends(get_socratic_engine)]


def get_analytics_evaluator(llm: LLMDep) -> AnalyticsEvaluator:
    return AnalyticsEvaluator(llm=llm)


AnalyticsDep = Annotated[AnalyticsEvaluator, Depends(get_analytics_evaluator)]


def get_context_builder() -> ContextBuilder:
    return ContextBuilder()


ContextBuilderDep = Annotated[ContextBuilder, Depends(get_context_builder)]


def get_personalization_director() -> PersonalizationDirector:
    return PersonalizationDirector()


DirectorDep = Annotated[PersonalizationDirector, Depends(get_personalization_director)]
