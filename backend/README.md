# DEP-PM Backend

FastAPI + SQLAlchemy 2.x + Alembic backend for the DEP-PM Platform. Sprint 1 (Foundation).

## Setup

```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate   |   *nix: source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # fill in ANTHROPIC_API_KEY to enable the PM Agent
```

## Run

```bash
alembic upgrade head          # create schema + seed the Claude Solo agent (SQLite dev)
uvicorn app.main:app --reload # http://127.0.0.1:8000  (docs at /docs)
```

## Test

```bash
pytest
```

## Key endpoints (Blueprint §13)

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/api/projects` | Create project (new / existing) |
| GET/POST | `/api/projects/:id/tasks` | List / create tasks |
| POST | `/api/projects/:id/breakdown` | PM Agent: requirement → backlog tasks |
| POST | `/api/projects/:id/confirm` | Confirm scope: backlog → planned |
| POST | `/api/projects/:id/scan` | Brownfield metadata scan (stub, ADR-02) |
| PATCH | `/api/tasks/:id` | Update status / assignee |
| GET | `/api/tasks/:id/messages` | Inter-agent message history |

## Notes

- **No `ANTHROPIC_API_KEY`?** `/breakdown` still works — it returns a single fallback task
  and `source: "fallback"`. Set the key to get real PM Agent decomposition.
- **DB:** SQLite for dev; switch `DATABASE_URL` to PostgreSQL for staging/prod (ADR-01). All
  columns use portable types (`GUID`, `JSON`) so no model changes are needed.
- Full State Machine validation and the Orchestrator runtime land in Sprint 2.
