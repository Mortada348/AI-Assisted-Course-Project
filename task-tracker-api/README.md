# Task Tracker API

A learning-focused REST API built with **FastAPI** and **Pydantic**, plus a
static vanilla-JS Kanban frontend that consumes it. Supports creating,
viewing, filtering, updating, and deleting tasks, including restricted
status transitions and tag management.

Storage is **in-memory only** (a module-level dict in `app/storage.py`) —
all data is lost on process restart. There is no database and no file-based
persistence, despite an earlier version of this README referencing
"ADR-001"; no such document exists in this repo. [VERIFY]

This is a learning project. It is not deployed anywhere, has no
authentication or user accounts, and is not intended for production use.

## Prerequisites

- Python 3.11+ (CI and the Dockerfile both use 3.11; no minimum has been
  verified for local development) [VERIFY]
- `pip`
- Docker, only if you want to run the containerized build

## Local setup

Run all commands below from the `task-tracker-api/` directory.

```
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

On macOS/Linux, activate with `source venv/bin/activate` instead.

A `.env.example` is provided with the default settings (`PORT=8000`,
`APP_ENV=development`); copy it to `.env` if you don't already have one:

```
cp .env.example .env
```

## Run the app locally

```
uvicorn app.main:app --reload --port 8000
```

The API is then available at `http://localhost:8000`, with interactive
docs at `http://localhost:8000/docs` and a health check at
`http://localhost:8000/health`.

## Run tests

```
pytest -v
```

`tests/verify_a.py` is a standalone script for manually exercising
`TaskCreate`/`TaskUpdate` validation edge cases — run it with `python`, not
`pytest`, since it prints PASS/FAIL rather than using assertions:

```
python tests/verify_a.py
```

## Run with Docker

Build and run from `task-tracker-api/` (the Dockerfile's `COPY` paths are
relative to this directory):

```
docker build -t task-tracker-api .
docker run --rm -p 8000:8000 task-tracker-api
```

The image only copies `app/` (see `Dockerfile` and `.dockerignore`) — it
does not include `.env`, `tests/`, or `frontend/`. Without a `.env` file,
`Settings` falls back to its defaults (`PORT=8000`, `APP_ENV=development`),
which match the container's exposed port, so no extra configuration is
needed for a default run.

## CI workflow summary

Defined in `.github/workflows/ci.yml` (at the outer repository root, one
level above `task-tracker-api/`). On every `push` and `pull_request`, the
`test` job:

1. Checks out the repository.
2. Sets up Python 3.11.
3. Caches pip downloads keyed on `requirements.txt`.
4. Installs dependencies with `pip install -r requirements.txt`.
5. Runs `pytest -v --tb=short`.

All steps run with `working-directory: task-tracker-api`. There is no
build, lint, deploy, or publish step — this pipeline only runs tests.

## Project structure

```
task-tracker-api/
├── app/
│   ├── main.py            # FastAPI app instance; task endpoints defined inline
│   ├── models.py          # TaskCreate / TaskUpdate / TaskResponse Pydantic models
│   ├── storage.py         # In-memory task storage
│   ├── business_rules.py  # Status-transition and tag validation rules
│   ├── api/
│   │   └── health.py      # Health-check router
│   ├── schemas/
│   │   └── health.py      # Health-check response schema
│   └── core/
│       └── config.py      # .env-backed settings (PORT, APP_ENV)
├── tests/
│   ├── conftest.py        # `client` / `created_task` fixtures, storage reset
│   ├── test_tasks.py       # Pytest suite
│   └── verify_a.py        # Standalone validation script (run with `python`, not pytest)
├── frontend/                # Static HTML/CSS/JS Kanban board, no build step
├── Dockerfile
├── requirements.txt
└── pytest.ini
```

## Project conventions and current limitations

- **In-memory storage only.** All tasks live in a module-level dict in
  `app/storage.py` and are lost on restart; `storage._reset()` is used by
  an autouse fixture in `tests/conftest.py` to isolate tests.
- **Two endpoint patterns coexist.** `/health` uses an `APIRouter`
  (`app/api/health.py`) included via `app.include_router(...)`; the
  `/tasks` endpoints are defined directly on the `app` instance in
  `app/main.py`. New task-related endpoints should follow the inline
  pattern used by the existing task routes.
- **Strict request validation.** `TaskCreate`, `TaskUpdate`, and
  `TaskResponse` all set `extra="forbid"`, so unknown fields in a request
  body return `422`.
- **Restricted status transitions.** Only `ToDo→InProgress`,
  `InProgress→Done`, and `Done→InProgress` are allowed
  (`app/business_rules.py`); any other transition, including re-setting
  the current status, returns `422`.
- **Frontend is a separate static app.** `frontend/` has no build step and
  talks to the API via a hardcoded `backendBaseUrl = "http://localhost:8000"`
  in `frontend/javascript.js`. CORS in `app/main.py` currently only allows
  `localhost:5500`/`127.0.0.1:5500` (e.g. VS Code Live Server) and
  `localhost:5173` (Vite); update `allow_origins` to serve the frontend
  from elsewhere.
- **No auth, no database, no deployment.** There are no user accounts, no
  persistence beyond the process lifetime, and no deployment
  configuration in this repo.

## Docs / decision records

No architecture decision record or technical design note currently exists
in this repository. [VERIFY] An earlier version of this README referenced
"ADR-001" for JSON file storage, but no such file was found under `docs/`
or elsewhere; the only files present there are course-deliverable
documents (prompt log, reflection, user stories, verification), not
technical notes. If an ADR is added later, link it here.
