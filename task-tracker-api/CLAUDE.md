# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

Task Tracker API: a learning-focused REST API built with FastAPI + Pydantic, plus a static vanilla-JS Kanban frontend that consumes it. Endpoints support creating, viewing, filtering, updating, and deleting tasks.

## Commands

Run from `task-tracker-api/` with the venv active (`venv\Scripts\activate` on Windows).

```
pip install -r requirements.txt        # install deps
uvicorn app.main:app --reload          # run the API (defaults to port 8000, see .env)
pytest                                 # run the full test suite
pytest tests/test_tasks.py::test_name  # run a single test
python tests/verify_a.py               # ad-hoc Pydantic model checks (not a pytest file — prints PASS/FAIL, no assertions)
```

The frontend (`frontend/`) is static HTML/CSS/JS with no build step or package.json — open `index.html` directly or serve it with any static server. It talks to the API at a hardcoded `backendBaseUrl = "http://localhost:8000"` in `frontend/javascript.js`. CORS in `app/main.py` is currently locked to `localhost:5500`/`127.0.0.1:5500` (e.g. VS Code Live Server) and `localhost:5173` (Vite) — update `allow_origins` if serving the frontend elsewhere.

## Architecture

**Storage is in-memory, not JSON files.** `app/storage.py` holds tasks in a module-level `_tasks: dict[str, TaskResponse]`. This contradicts the README's claim of "local JSON file storage (see ADR-001)" — no ADR docs or file-backed persistence currently exist in this branch; treat the README's storage claim as aspirational/stale, not current behavior. All data is lost on process restart. `storage._reset()` clears state and is used by the autouse `_reset_storage` fixture in `tests/conftest.py` to isolate tests.

**Two different endpoint patterns coexist:**
- Health check follows a router pattern: `app/api/health.py` defines an `APIRouter`, with its response schema in `app/schemas/health.py`, included into the app via `app.include_router(...)` in `app/main.py`.
- Task endpoints (`/tasks`, `/tasks/{id}`) are defined directly on the `app` instance inline in `app/main.py`, using models from `app/models.py` (not `app/schemas/`). When adding new task-related endpoints, match whichever pattern the surrounding code already follows rather than mixing further — but note the existing task endpoints are inline, not router-based.

**Task model** (`app/models.py`): `TaskCreate`/`TaskUpdate`/`TaskResponse` all set `extra="forbid"`, so unknown fields in request bodies return 422. `title` is validated (stripped, non-blank, ≤200 chars) on both create and update via `field_validator`. `TaskStatus` (`ToDo`/`InProgress`/`Done`) and `TaskPriority` (`Low`/`Medium`/`High`) are string enums — their values (not Python names) are what the API and frontend exchange.

**Status transitions are restricted**, not free-form. `app/business_rules.py` defines `VALID_TRANSITIONS` as an explicit allow-list: `ToDo→InProgress`, `InProgress→Done`, `Done→InProgress`. Anything else — including patching a task to its current status — raises 422. This is checked in `PATCH /tasks/{id}` in `app/main.py` only when `payload.status` is set, before delegating to `storage.update_task`.

**Config** (`app/core/config.py`): loads `.env` via `python-dotenv` into a single shared `settings` instance (`settings.app_env`, `settings.port`). `.env`/`.env.example` currently define `PORT` and `APP_ENV`.

**Tests** (`tests/`): `pytest.ini` sets `pythonpath = .` so `app` imports work without installing the package. `tests/conftest.py` provides `client` (a `TestClient` over `app.main.app`) and `created_task` (a task created via a real POST) fixtures, plus the autouse storage reset. `tests/verify_a.py` is a standalone script (run with `python`, not `pytest`) for manually exercising `TaskCreate`/`TaskUpdate` validation edge cases.
