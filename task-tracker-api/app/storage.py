import uuid
from datetime import datetime, timezone
from typing import Optional

from app.business_rules import (
    is_task_overdue,
    validate_tag_removal,
    validate_no_duplicate_tags,
)
from app.models import TaskCreate, TaskPriority, TaskResponse, TaskStatus, TaskUpdate

_tasks: dict[str, TaskResponse] = {}


def _with_computed_overdue(task: TaskResponse) -> TaskResponse:
    overdue = is_task_overdue(task.due_date, task.status)
    if overdue == task.is_overdue:
        return task
    return task.model_copy(update={"is_overdue": overdue})


def add_task(payload: TaskCreate) -> TaskResponse:
    """Create and store a new task from validated input.

    Args:
        payload: Validated task-creation data.

    Returns:
        TaskResponse: The newly stored task, with a generated `id`,
        `created_at`/`updated_at` timestamps, and computed `is_overdue`.
    """
    now = datetime.now(timezone.utc)
    task_id = str(uuid.uuid4())
    task = TaskResponse(
        id=task_id,
        title=payload.title,
        description=payload.description or "",
        status=payload.status,
        priority=payload.priority,
        assignee=payload.assignee,
        tags=payload.tags,
        due_date=payload.due_date,
        created_at=now,
        updated_at=now,
    )
    task = _with_computed_overdue(task)
    _tasks[task_id] = task
    return task


def get_all_tasks(
    status: Optional[TaskStatus] = None,
    priority: Optional[TaskPriority] = None,
    not_overdue: Optional[bool] = None,
) -> list[TaskResponse]:
    """Return all stored tasks, optionally filtered.

    Args:
        status: Only include tasks with this status. If None, no
            status filtering is applied.
        priority: Only include tasks with this priority. If None, no
            priority filtering is applied.
        not_overdue: If True, only include tasks that have a due date and
            are not overdue. If None or False, no overdue-based filtering
            is applied.

    Returns:
        list[TaskResponse]: Matching tasks, each with `is_overdue`
        recomputed against the current date.
    """
    tasks = [_with_computed_overdue(t) for t in _tasks.values()]
    if status is not None:
        tasks = [t for t in tasks if t.status == status]
    if priority is not None:
        tasks = [t for t in tasks if t.priority == priority]
    if not_overdue is True:
        tasks = [t for t in tasks if t.due_date is not None and not t.is_overdue]
    return tasks


def get_task_by_id(task_id: str) -> Optional[TaskResponse]:
    """Look up a single task by id.

    Args:
        task_id: The id of the task to look up.

    Returns:
        Optional[TaskResponse]: The task with `is_overdue` recomputed, or
        None if no task with that id exists.
    """
    task = _tasks.get(task_id)
    if task is None:
        return None
    return _with_computed_overdue(task)


def get_tasks_by_tag(tag: str) -> list[TaskResponse]:
    """Return all tasks with a tag exactly matching the given value.

    Args:
        tag: Tag to match, case-insensitively, against each task's tags.

    Returns:
        list[TaskResponse]: Tasks containing a tag equal to `tag`
        (case-insensitive comparison).
    """
    normalized = tag.strip().casefold()
    tasks = [_with_computed_overdue(t) for t in _tasks.values()]
    return [t for t in tasks if any((tg or "").casefold() == normalized for tg in (t.tags or []))]


def search_tasks_by_tag(query: str) -> list[TaskResponse]:
    """Return all tasks with a tag containing the given query.

    Args:
        query: Substring to search for, matched case-insensitively against
            each task's tags.

    Returns:
        list[TaskResponse]: Tasks with at least one tag that contains
        `query` (case-insensitive substring match).
    """
    normalized = query.strip().casefold()
    tasks = [_with_computed_overdue(t) for t in _tasks.values()]
    return [t for t in tasks if any(normalized in (tg or "").casefold() for tg in (t.tags or []))]


def update_task(task_id: str, payload: TaskUpdate) -> Optional[TaskResponse]:
    """Apply a partial update to a stored task.

    Args:
        task_id: The id of the task to update.
        payload: Fields to update; only fields explicitly set are applied.
            `add_tags` and `remove_tags` are handled separately from the
            other fields, modifying the task's tag list rather than
            replacing it.

    Returns:
        Optional[TaskResponse]: The updated task with a refreshed
        `updated_at` timestamp and recomputed `is_overdue`. Returns the
        unchanged task if no fields were set. Returns None if no task
        with `task_id` exists.

    Raises:
        HTTPException: 422 (via `validate_tag_removal`) if a tag in
            `payload.remove_tags` does not exist on the task.
    """
    task = _tasks.get(task_id)
    if task is None:
        return None
    updates = payload.model_dump(exclude_unset=True)
    # handle tag modifications separately so they are not passed through model_copy
    add_tags = updates.pop("add_tags", None)
    remove_tags = updates.pop("remove_tags", None)
    if not updates and add_tags is None and remove_tags is None:
        return task
    now = datetime.now(timezone.utc)

    # start from current tags
    current_tags: list[str] = list(task.tags or [])

    # handle removals (validate removes before changing)
    if remove_tags:
        for tag in remove_tags:
            validate_tag_removal(current_tags, tag)
        # remove any matching tags (case-insensitive)
        removal_set = {t.casefold() for t in remove_tags}
        current_tags = [t for t in current_tags if t.casefold() not in removal_set]

    # handle additions (skip duplicates case-insensitively)
    if add_tags:
        cleaned = validate_no_duplicate_tags(add_tags)
        existing_set = {t.casefold() for t in current_tags}
        for tag in cleaned:
            if tag.casefold() in existing_set:
                continue
            current_tags.append(tag)
            existing_set.add(tag.casefold())

    updated = task.model_copy(update={**updates, "tags": current_tags, "updated_at": now})
    updated = _with_computed_overdue(updated)
    _tasks[task_id] = updated
    return updated


def delete_task(task_id: str) -> bool:
    """Delete a task by id.

    Args:
        task_id: The id of the task to delete.

    Returns:
        bool: True if a task was found and deleted, False if no task with
        that id existed.
    """
    if task_id not in _tasks:
        return False
    del _tasks[task_id]
    return True


def _reset() -> None:
    _tasks.clear()
