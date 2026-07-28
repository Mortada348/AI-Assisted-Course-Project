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
        "Storage is in-memory only (a module-level dict); all data is "
        "lost on process restart."
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
    """List tasks, optionally filtered by status, priority, overdue state, or tag.

    Args:
        status: Only include tasks with this status. If None, tasks of any
            status are included.
        priority: Only include tasks with this priority. If None, tasks of
            any priority are included.
        not_overdue: If True, only include tasks that have a due date and
            are not overdue. If None or False, no overdue-based filtering
            is applied.
        tag: If provided, first restrict results to tasks with a tag that
            case-insensitively matches this value, then apply the other
            filters on top.

    Returns:
        list[TaskResponse]: Tasks matching the given filters.

    Example:
        GET /tasks?status=ToDo&priority=High&tag=backend
    """
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
    """Search tasks by tag, matching on substring rather than exact tag value.

    Args:
        tag: Substring to search for, matched case-insensitively against
            each task's tags.

    Returns:
        list[TaskResponse]: Tasks with at least one tag that contains
        `tag` (case-insensitive substring match).

    Example:
        GET /tasks/search?tag=back
    """
    tasks = storage.search_tasks_by_tag(tag)
    print(f"[GET /tasks/search] Returning {len(tasks)} tasks for tag '{tag}': {[t.model_dump() for t in tasks]}")
    return tasks


@app.post("/tasks", response_model=TaskResponse, status_code=status.HTTP_201_CREATED, tags=["tasks"])
def create_task(payload: TaskCreate) -> TaskResponse:
    """Create a new task.

    Args:
        payload: Task fields to create, validated by `TaskCreate` (e.g.
            non-blank title of at most 200 characters, deduplicated tags,
            and a `due_date` that must be in the future).

    Returns:
        TaskResponse: The newly created task, including its generated id
        and timestamps.

    Example:
        POST /tasks
        {"title": "Write docs", "priority": "High"}
    """
    return storage.add_task(payload)


@app.get("/tasks/{task_id}", response_model=TaskResponse, tags=["tasks"])
def get_task(task_id: str) -> TaskResponse:
    """Retrieve a single task by id.

    Args:
        task_id: The id of the task to retrieve.

    Returns:
        TaskResponse: The matching task.

    Raises:
        HTTPException: 404 if no task exists with the given `task_id`.

    Example:
        GET /tasks/3fa85f64-5717-4562-b3fc-2c963f66afa6
    """
    task = storage.get_task_by_id(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail=f"Task with id {task_id} not found")
    return task


@app.patch("/tasks/{task_id}", response_model=TaskResponse, tags=["tasks"])
def update_task(task_id: str, payload: TaskUpdate) -> TaskResponse:
    """Partially update a task, applying only the fields explicitly set on the payload.

    Args:
        task_id: The id of the task to update.
        payload: Fields to update. Only fields explicitly set on `payload`
            are applied; unset fields leave the existing value unchanged.
            May include a `status` change, tag additions (`add_tags`), or
            tag removals (`remove_tags`).

    Returns:
        TaskResponse: The updated task.

    Raises:
        HTTPException: 404 if no task exists with the given `task_id`.
        HTTPException: 422 if `payload.status` equals the task's current
            status, or if the requested status transition is not one of
            the allowed transitions in `business_rules.VALID_TRANSITIONS`.
        HTTPException: 422 if any tag in `payload.remove_tags` does not
            exist on the task (raised by `validate_tag_removal`).

    Example:
        PATCH /tasks/3fa85f64-5717-4562-b3fc-2c963f66afa6
        {"status": "InProgress"}
    """
    updates = payload.model_dump(exclude_unset=True)
    existing: TaskResponse | None = None
    if payload.status is not None or any(key in updates for key in ("remove_tags", "add_tags")):
        existing = storage.get_task_by_id(task_id)
        if existing is None:
            raise HTTPException(status_code=404, detail=f"Task with id {task_id} not found")
    if payload.status is not None and existing is not None:
        if payload.status == existing.status:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Status is already {payload.status.value}",
            )
        validate_status_transition(existing.status, payload.status)
    if existing is not None:
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
    """Delete a task by id.

    Args:
        task_id: The id of the task to delete.

    Returns:
        None: Responds with 204 No Content on success.

    Raises:
        HTTPException: 404 if no task exists with the given `task_id`.

    Example:
        DELETE /tasks/3fa85f64-5717-4562-b3fc-2c963f66afa6
    """
    if not storage.delete_task(task_id):
        raise HTTPException(status_code=404, detail=f"Task with id {task_id} not found")


@app.on_event("startup")
def on_startup() -> None:
    """Log the environment and port the app is starting with.

    Returns:
        None
    """
    print(f"Starting Task Tracker API in '{settings.app_env}' mode on port {settings.port}")


