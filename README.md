# BrainEcosystem 🌱

**A Scalable Modular Holistic Learning Companion for Indian Schools**

BrainEcosystem is a production-grade, open-source AI-powered educational platform that delivers Socratic, inquiry-driven, embodied learning aligned with NEP 2020. It grows from MVP to a full school ecosystem (students, teachers, admins, parents) while remaining modular and independently extensible.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                     BRAINECOSYSTEM CORE                              │
│                                                                     │
│  ┌──────────────────┐  ┌────────────────────┐  ┌────────────────┐  │
│  │  student_model   │  │ socratic_adaptive  │  │curriculum_mapper│  │
│  │  ─────────────   │  │     _engine        │  │ ─────────────  │  │
│  │  - Holistic      │◄─┤  ─────────────     │  │ - ConceptGraph │  │
│  │    profile       │  │  - SocraticGuard   │  │ - CurriculumReg│  │
│  │  - SM-2 SR       │  │  - DialogueMgr     │  │ [PLUGGABLE]    │  │
│  │  - Mastery map   │  │  - AdaptivePath    │  └───────┬────────┘  │
│  └──────────────────┘  └────────────────────┘          │           │
│           │                                             │           │
│  ┌────────▼────────┐  ┌────────────────────┐  ┌────────▼────────┐  │
│  │ personalization │  │multimodal_context  │  │   simulator     │  │
│  │   _director     │  │ ─────────────────  │  │ ─────────────  │  │
│  │  ─────────────  │  │  - LLMProvider     │  │  - RobotSim    │  │
│  │  - DailyPlan    │  │  - ContextBuilder  │  │  - PhysicsSim  │  │
│  │  - FocusCues    │  │  - Vision (future) │  │  [PLUGGABLE]   │  │
│  │  - WeeklyGoal   │  └────────────────────┘  └────────────────┘  │
│  └─────────────────┘                                               │
│           │                                                         │
│  ┌────────▼─────────────────────────────────────────────────────┐  │
│  │                    analytics_evaluation                        │  │
│  │  RubricEvaluator (Bloom's) · HolisticMetricsEngine · NEP     │  │
│  └────────────────────────────────────────────────────────────── ┘  │
└─────────────────────────────────────────────────────────────────────┘
           │                   │                  │               │
   ┌───────▼──┐       ┌───────▼──┐      ┌────────▼──┐  ┌───────▼──┐
   │ STUDENT  │       │ TEACHER  │      │   ADMIN   │  │  PARENT  │
   │  Layer   │       │  Layer   │      │   Layer   │  │  Layer   │
   │──────────│       │──────────│      │───────────│  │──────────│
   │ Chat     │       │ Heatmaps │      │ NEP Report│  │ Weekly   │
   │ Simulator│       │ Lesson   │      │ Equity    │  │ Growth   │
   │ DailyPlan│       │ Rubrics  │      │ Analytics │  │ Story    │
   └──────────┘       └──────────┘      └───────────┘  └──────────┘

                    ┌─────────────────────────────┐
                    │        PLUGINS              │
                    │  school/ · jee/ · future/   │
                    │  [Register at startup]      │
                    └─────────────────────────────┘
```

### Scalability Considerations

| Concern | MVP | Production Path |
|---------|-----|-----------------|
| Database | SQLite (aiosqlite) | PostgreSQL + AsyncPG + PgBouncer |
| LLM | Ollama local | Load-balanced llama.cpp cluster / vLLM |
| Caching | None (hooks ready) | Redis per-student profile cache |
| Analytics | Inline (sync) | Celery/ARQ background workers |
| Multi-tenant | tenant_id column | Row-level security + Postgres schemas |
| Concept graph | NetworkX in-memory | Neo4j for >10k concepts |
| Frontend state | Zustand | Same (scales fine) |

---

## Project Structure

```
brainecosystem/
├── src/
│   ├── core/
│   │   ├── config.py                   # Pydantic Settings, env-driven
│   │   ├── database.py                 # Async SQLAlchemy engine
│   │   ├── logging_config.py           # structlog + correlation IDs
│   │   ├── student_model/              # Holistic student profile + SM-2 SR
│   │   ├── socratic_adaptive_engine/   # Dialogue + guard + adaptive path
│   │   ├── curriculum_mapper/          # Concept graph + plugin registry
│   │   ├── personalization_director/   # Daily/weekly plans + focus cues
│   │   ├── simulator/                  # Robot + physics simulators
│   │   ├── multimodal_context/         # LLM provider + context builder
│   │   └── analytics_evaluation/       # Rubrics + holistic metrics
│   ├── plugins/
│   │   ├── school/curriculum.py        # NEP Grades 6–8 with India context
│   │   └── jee/curriculum.py           # JEE conceptual depth plugin
│   └── api/
│       ├── main.py                     # FastAPI app + lifespan
│       ├── dependencies.py             # DI providers
│       ├── student/routes.py           # Chat, simulator, daily plan
│       ├── teacher/routes.py           # Insights, lesson generation
│       ├── admin/routes.py             # NEP report, equity analytics
│       └── parent/routes.py            # Weekly narrative report
├── frontend/
│   └── src/
│       ├── components/
│       │   ├── chat/ChatPage.tsx       # Socratic dialogue UI
│       │   ├── simulator/              # Robot canvas + controls
│       │   ├── dashboard/DashboardPage.tsx
│       │   └── teacher/TeacherDashboard.tsx
│       ├── lib/api.ts                  # Typed API client
│       └── stores/sessionStore.ts      # Zustand state
├── tests/
│   └── core/                           # Unit tests for all core modules
├── docker/
├── docker-compose.yml
├── pyproject.toml
└── .env.example
```

---

## Quick Start

### Prerequisites
- Python 3.12+
- Node 20+
- [Ollama](https://ollama.com) (for local LLM)
- Docker (optional but recommended)

### 1. Clone and configure

```bash
git clone https://github.com/your-org/brainecosystem
cd brainecosystem
cp .env.example .env
# Edit .env — set APP_SECRET_KEY, DATABASE_URL, etc.
```

### 2. Backend (local dev)

```bash
pip install -e ".[dev]"

# Pull the LLM model (one-time, ~2GB)
ollama pull llama3.2:3b

# Run the API
uvicorn src.api.main:app --reload --port 8000
```

The API starts at `http://localhost:8000`. OpenAPI docs: `http://localhost:8000/docs`

### 3. Frontend

```bash
cd frontend
npm install
npm run dev
# Opens at http://localhost:5173
```

### 4. Full stack with Docker

```bash
docker-compose up --build
# API: http://localhost:8000
# Frontend: http://localhost:5173
# Ollama pulls llama3.2:3b automatically on first run
```

### 5. Run tests

```bash
pytest -v --cov=src
```

---

## Core Concepts

### Socratic Guard

The `SocraticGuard` in `src/core/socratic_adaptive_engine/guards.py` is a **non-negotiable safety layer** that screens every LLM response before it reaches the student. It:

- Blocks any response matching direct-answer patterns ("the answer is…", "here is the solution…")
- Enforces that every response contains at least one inquiry question
- Falls back to a contextual redirect if the LLM tries to short-circuit learning

```python
guard = SocraticGuard()
result = guard.check(llm_output)
if not result.passed:
    use(result.sanitised_text)  # always safe to use
```

### SM-2 Spaced Repetition

The student model uses a SM-2 variant to schedule concept reviews:

- Quality score (0–5) derived from mastery delta + reasoning correctness
- Ease factor adjusts per performance
- `next_review_at` stored per `ConceptMastery` row
- Daily plan surfaces due reviews before new content

### Holistic Markers

Every student has a `HolisticMarkers` record updated via EMA after each session:

| Marker | What it measures |
|--------|-----------------|
| `avg_reasoning_quality` | Depth of reasoning in LLM-scored responses |
| `avg_reflection_depth` | How deeply students reflect at session end |
| `avg_focus_signal` | Engagement signal (future: vision-based) |
| `ethical_moments_count` | Organic ethical reasoning instances |
| `streak_days` | Consecutive days of learning |
| `resilience_score` | Persistence through difficult concepts |

---

## Adding a New Curriculum Segment

1. Create `src/plugins/your_segment/curriculum.py`
2. Implement `CurriculumPlugin`:

```python
from src.core.curriculum_mapper.interfaces import CurriculumPlugin, ConceptNode

class EngineeringPlugin(CurriculumPlugin):
    @property
    def segment_id(self) -> str:
        return "engineering"

    @property
    def supported_grades(self) -> list[str]:
        return ["12", "UG1", "UG2"]

    def get_concept(self, concept_id: str) -> ConceptNode | None:
        ...  # return from your concept catalog

    # Implement other abstract methods
```

3. Register in `src/api/main.py` lifespan:

```python
from src.plugins.engineering.curriculum import EngineeringPlugin
curriculum.register(EngineeringPlugin())
```

That's it — no core changes needed.

---

## Adding a New Simulator

1. Create `src/core/simulator/your_sim.py` implementing `SimulatorInterface`
2. Register in `main.py`:

```python
from src.core.simulator.your_sim import YourSimulator
simulators.register(YourSimulator())
```

The frontend `SimulatorPage` and `/api/v1/student/simulator/command` endpoint automatically support it.

---

## API Reference

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/student/profile` | POST | Create/get student |
| `/api/v1/student/daily-plan/{id}` | GET | Get personalised daily plan |
| `/api/v1/student/chat` | POST | Socratic dialogue turn |
| `/api/v1/student/simulator/command` | POST | Execute simulator command |
| `/api/v1/student/session/open` | POST | Start a learning session |
| `/api/v1/student/session/{id}/close` | POST | Close session + update metrics |
| `/api/v1/teacher/classroom/{tid}/grade/{g}/insights` | GET | Mastery heatmap |
| `/api/v1/teacher/lesson-plan` | POST | AI-generated lesson plan |
| `/api/v1/teacher/rubric/generate` | POST | Assessment rubric |
| `/api/v1/admin/tenant/{id}/nep-report` | GET | NEP compliance report |
| `/api/v1/admin/tenant/{id}/equity-report` | GET | At-risk student analytics |
| `/api/v1/parent/report/{id}` | GET | Weekly narrative parent report |
| `/health` | GET | LLM + system health |

---

## Phased Roadmap

### Phase 1 (Weeks 1–2) — Core Foundation ✅
- [x] All 7 core shared modules with clean interfaces
- [x] School plugin (Grades 6–8, NCERT-aligned, India context)
- [x] JEE plugin (conceptual depth, Grade 11–12)
- [x] Robot + Physics simulators
- [x] Full FastAPI REST API (student/teacher/admin/parent)
- [x] React frontend (chat, simulator, dashboard, teacher view)
- [x] Test suite covering all core modules

### Phase 2 (Weeks 3–4) — Experience Polish
- [ ] JWT authentication + role-based access
- [ ] Real-time websocket chat (replace REST polling)
- [ ] Vision engagement detection (LLaVA via Ollama)
- [ ] Simulator: Circuit builder, Chemistry lab
- [ ] Parent mobile app (React Native / PWA)
- [ ] Alembic migrations for schema evolution

### Phase 3 (Weeks 5–8) — School Operations
- [ ] Teacher gradebook integration
- [ ] Bulk student import (CSV / school SIS API)
- [ ] Multi-school SaaS admin panel
- [ ] Automated parent WhatsApp reports
- [ ] NEP report PDF export
- [ ] Redis session caching + background analytics workers

### Phase 4 (Months 3–6) — Ecosystem Scale
- [ ] Hardware integration (actual robot via Bluetooth/MQTT)
- [ ] Offline-capable Progressive Web App
- [ ] Custom concept authoring tool for teachers
- [ ] Vernacular language support (Hindi, Tamil, Telugu)
- [ ] Advanced spaced repetition (FSRS algorithm)
- [ ] Benchmark dataset for holistic growth measurement

---

## Scaling for Production

### Database

```bash
# Switch from SQLite to Postgres — just change .env
DATABASE_URL=postgresql+asyncpg://user:pass@db:5432/brainecosystem

# Run Alembic migrations
alembic upgrade head
```

### LLM at Scale

```yaml
# docker-compose.yml — add GPU support to ollama service
deploy:
  resources:
    reservations:
      devices:
        - driver: nvidia
          count: 1
          capabilities: [gpu]
```

For 100+ concurrent students: deploy vLLM with `llama3.2:3b` and point `LLM_BASE_URL` at it. The `OllamaProvider` is OpenAI-API-compatible so vLLM works out of the box.

### Multi-Tenancy

Each school has its own `tenant_id`. Row-level filtering is enforced in every query. For full isolation in production, enable PostgreSQL Row Level Security:

```sql
ALTER TABLE student_profiles ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON student_profiles
  USING (tenant_id = current_setting('app.tenant_id'));
```

### Background Analytics

Install ARQ (async Redis Queue) and move `_aggregate_holistic_markers` and `evaluate_student_response` calls to background tasks:

```python
# In session close endpoint:
await arq_pool.enqueue_job("aggregate_markers", student_id, summary.dict())
```

---

## Contributing

1. Fork the repository
2. Follow the module structure — new features go in the right layer
3. Write tests for all new core logic
4. Run `ruff check . && mypy src/` before submitting a PR

---

## Philosophy

> "Tell me and I forget. Teach me and I remember. Involve me and I learn." — Benjamin Franklin (paraphrasing Confucius)

BrainEcosystem is built on the conviction that India's students are capable of genuine understanding — not just exam performance. The Socratic guard is not a UX choice; it is a pedagogical commitment. Every design decision should ask: *does this help the student think, or does it think for them?*

---

## License

MIT — see `LICENSE` for details.
