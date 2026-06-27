"""BrainEcosystem FastAPI application entry point.

Lifespan context manager handles startup/shutdown cleanly:
  - Initialises LLM provider (connection pool)
  - Registers curriculum and simulator plugins
  - Creates DB tables (MVP; use Alembic for prod)
  - Wires Redis cache (if configured)
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.core.config import get_settings
from src.core.database import create_all_tables
from src.core.logging_config import configure_logging, get_logger
from src.core.multimodal_context.llm_provider import LLMProvider, OllamaProvider
from src.core.multimodal_context.mock_llm import MockLLMProvider
from src.core.multimodal_context.claude_provider import ClaudeProvider
from src.core.curriculum_mapper.registry import CurriculumRegistry
from src.core.simulator.registry import SimulatorRegistry
from src.core.simulator.robot_sim import RobotSimulator
from src.core.simulator.physics_sim import PhysicsSimulator
from src.plugins.school.curriculum import SchoolCurriculumPlugin
from src.plugins.jee.curriculum import JEECurriculumPlugin

from .student.routes import router as student_router
from .teacher.routes import router as teacher_router
from .admin.routes import router as admin_router
from .parent.routes import router as parent_router

settings = get_settings()
configure_logging(settings.log_level, settings.log_format)
log = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    log.info("brainecosystem_starting", env=settings.app_env)

    # LLM provider — selected by LLM_PROVIDER env var, falls back to mock on failure
    llm: LLMProvider
    if settings.llm.provider == "mock":
        llm = MockLLMProvider()
        log.info("llm_provider", mode="mock")
    elif settings.llm.provider == "claude":
        try:
            llm = ClaudeProvider()
            if not await llm.health_check():
                log.warning("claude_health_check_failed", fallback="mock")
                llm = MockLLMProvider()
            else:
                log.info("llm_provider", mode="claude", model=settings.llm.model)
        except ValueError as exc:
            log.warning("claude_config_error", error=str(exc), fallback="mock")
            llm = MockLLMProvider()
    else:
        llm = OllamaProvider()
        if not await llm.health_check():
            log.warning("ollama_unreachable", fallback="mock")
            llm = MockLLMProvider()
        else:
            log.info("llm_provider", mode="ollama", model=settings.llm.model)
    app.state.llm = llm

    # Curriculum registry
    curriculum = CurriculumRegistry()
    curriculum.register(SchoolCurriculumPlugin())
    curriculum.register(JEECurriculumPlugin())
    app.state.curriculum_registry = curriculum

    # Simulator registry
    simulators = SimulatorRegistry()
    simulators.register(RobotSimulator())
    simulators.register(PhysicsSimulator())
    app.state.simulator_registry = simulators

    # Database
    await create_all_tables()

    log.info("brainecosystem_ready", segments=curriculum.list_segments())
    yield

    # Cleanup
    await llm.aclose()
    log.info("brainecosystem_shutdown")


app = FastAPI(
    title="BrainEcosystem API",
    description="Scalable modular holistic learning companion for Indian schools",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.app_debug else None,
    redoc_url="/redoc" if settings.app_debug else None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.app_debug else ["https://yourdomain.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routes ─────────────────────────────────────────────────────────────────────
app.include_router(student_router, prefix="/api/v1/student", tags=["student"])
app.include_router(teacher_router, prefix="/api/v1/teacher", tags=["teacher"])
app.include_router(admin_router, prefix="/api/v1/admin", tags=["admin"])
app.include_router(parent_router, prefix="/api/v1/parent", tags=["parent"])


@app.get("/health", tags=["system"])
async def health_check() -> JSONResponse:
    llm_ok = await app.state.llm.health_check()
    return JSONResponse(
        content={
            "status": "ok" if llm_ok else "degraded",
            "llm": "up" if llm_ok else "down",
            "segments": app.state.curriculum_registry.list_segments(),
        }
    )


@app.get("/api/v1/simulators", tags=["simulators"])
async def list_simulators() -> JSONResponse:
    return JSONResponse(content=app.state.simulator_registry.list_simulators())
