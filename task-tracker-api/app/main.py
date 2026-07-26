"""
Application entry point.

Creates the FastAPI application instance and registers all API routers.
Run with: uvicorn app.main:app --reload
"""
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

from app.api.health import router as health_router
from app import storage
from app.business_rules import validate_status_transition, validate_tag_removal
from app.models import TaskCreate, TaskPriority, TaskResponse, TaskStatus, TaskUpdate
from app.core.config import settings

# Create the FastAPI application instance.
app = FastAPI(
    title="Task Tracker API",
    description=(
        "A learning-focused REST API for creating, viewing, filtering, "
        "updating, assigning, validating, and deleting tasks. "
        "Uses JSON file storage as described in ADR-001."
    ),
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5500",
        "http://127.0.0.1:5500",
        "http://localhost:5173",
        "null",
    ],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=False,
)

# Register the health-check router. Additional routers (tasks, etc.)
# will be added here as the project grows.
app.include_router(health_router)


@app.get("/tasks", response_model=list[TaskResponse], tags=["tasks"])
def list_tasks(
    status: TaskStatus | None = None,
    priority: TaskPriority | None = None,
    not_overdue: bool | None = None,
    tag: str | None = None,
) -> list[TaskResponse]:
    if tag is not None:
        tasks = storage.get_tasks_by_tag(tag)
        if status is not None:
            tasks = [t for t in tasks if t.status == status]
        if priority is not None:
            tasks = [t for t in tasks if t.priority == priority]
        if not_overdue is True:
            tasks = [t for t in tasks if t.due_date is not None and not t.is_overdue]
    else:
        tasks = storage.get_all_tasks(status=status, priority=priority, not_overdue=not_overdue)
    print(f"[GET /tasks] Returning {len(tasks)} tasks: {[t.model_dump() for t in tasks]}")
    return tasks


@app.get("/tasks/search", response_model=list[TaskResponse], tags=["tasks"])
def search_tasks(tag: str) -> list[TaskResponse]:
    tasks = storage.search_tasks_by_tag(tag)
    print(f"[GET /tasks/search] Returning {len(tasks)} tasks for tag '{tag}': {[t.model_dump() for t in tasks]}")
    return tasks


@app.post("/tasks", response_model=TaskResponse, status_code=status.HTTP_201_CREATED, tags=["tasks"])
def create_task(payload: TaskCreate) -> TaskResponse:
    return storage.add_task(payload)


@app.get("/tasks/{task_id}", response_model=TaskResponse, tags=["tasks"])
def get_task(task_id: str) -> TaskResponse:
    task = storage.get_task_by_id(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail=f"Task with id {task_id} not found")
    return task


@app.patch("/tasks/{task_id}", response_model=TaskResponse, tags=["tasks"])
def update_task(task_id: str, payload: TaskUpdate) -> TaskResponse:
    updates = payload.model_dump(exclude_unset=True)
    existing: TaskResponse | None = None
    if payload.status is not None or any(key in updates for key in ("tag_to_remove", "remove_tag", "remove_tags", "add_tags")):
        existing = storage.get_task_by_id(task_id)
        if existing is None:
            raise HTTPException(status_code=404, detail=f"Task with id {task_id} not found")
    if payload.status is not None and existing is not None:
        if payload.status != existing.status:
            validate_status_transition(existing.status, payload.status)
    if existing is not None:
        if "tag_to_remove" in updates:
            validate_tag_removal(existing.tags, updates["tag_to_remove"])
        if "remove_tag" in updates:
            validate_tag_removal(existing.tags, updates["remove_tag"])
        if "remove_tags" in updates:
            for tag in updates["remove_tags"]:
                validate_tag_removal(existing.tags, tag)
    task = storage.update_task(task_id, payload)
    if task is None:
        raise HTTPException(status_code=404, detail=f"Task with id {task_id} not found")
    print(f"[PATCH /tasks/{task_id}] Updated task: {task.model_dump()}")
    return task


@app.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["tasks"])
def delete_task(task_id: str) -> None:
    if not storage.delete_task(task_id):
        raise HTTPException(status_code=404, detail=f"Task with id {task_id} not found")


@app.on_event("startup")
def on_startup() -> None:
    """Log which environment the app is starting in (development/production)."""
    print(f"Starting Task Tracker API in '{settings.app_env}' mode on port {settings.port}")


