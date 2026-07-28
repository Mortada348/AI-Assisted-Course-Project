from fastapi import HTTPException, status
from datetime import date

from app.models import TaskStatus

VALID_TRANSITIONS: frozenset[tuple[TaskStatus, TaskStatus]] = frozenset({
    (TaskStatus.TODO, TaskStatus.IN_PROGRESS),
    (TaskStatus.IN_PROGRESS, TaskStatus.DONE),
    (TaskStatus.DONE, TaskStatus.IN_PROGRESS),
})


def validate_status_transition(current: TaskStatus, new: TaskStatus) -> None:
    """Validate that a status transition is allowed.

    Args:
        current: The task's current status.
        new: The status being transitioned to.

    Returns:
        None: Returns silently if the transition is allowed.

    Raises:
        HTTPException: 422 if `(current, new)` is not in `VALID_TRANSITIONS`.
            The error detail lists all allowed transitions.
    """
    if (current, new) not in VALID_TRANSITIONS:
        allowed = sorted({f"{f.value}->{t.value}" for f, t in VALID_TRANSITIONS})
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid status transition from {current.value} to {new.value}. Allowed transitions: {allowed}",
        )


def validate_tag(tag: str) -> str:
    """Validate and normalize a single tag.

    Args:
        tag: The raw tag string to validate.

    Returns:
        str: The tag with leading/trailing whitespace stripped.

    Raises:
        HTTPException: 422 if the stripped tag is empty.
    """
    stripped = tag.strip()
    if not stripped:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="tag cannot be blank",
        )
    return stripped


def validate_no_duplicate_tags(tags: list[str]) -> list[str]:
    """Remove case-insensitive duplicate tags, preserving first occurrence and original casing.

    Args:
        tags: List of tags to deduplicate.

    Returns:
        list[str]: Tags with case-insensitive duplicates removed, in
        original order.
    """
    cleaned_tags: list[str] = []
    seen: set[str] = set()
    for tag in tags:
        normalized = tag.casefold()
        if normalized in seen:
            continue
        seen.add(normalized)
        cleaned_tags.append(tag)
    return cleaned_tags


def validate_tag_removal(existing_tags: list[str], tag_to_remove: str) -> None:
    """Validate that a tag exists before it is removed.

    Args:
        existing_tags: The task's current tags.
        tag_to_remove: The tag requested for removal.

    Returns:
        None: Returns silently if the tag exists (case-insensitive match).

    Raises:
        HTTPException: 422 if no tag in `existing_tags` matches
            `tag_to_remove` case-insensitively.
    """
    normalized_target = tag_to_remove.strip().casefold()
    if not any(tag.casefold() == normalized_target for tag in existing_tags):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Tag '{tag_to_remove}' does not exist and cannot be removed",
        )


def is_task_overdue(due_date: date | None, status_: TaskStatus) -> bool:
    """Determine whether a task is overdue.

    Args:
        due_date: The task's due date, or None if it has no due date.
        status_: The task's current status.

    Returns:
        bool: False if `due_date` is None or `status_` is
        `TaskStatus.DONE`. Otherwise, True if `due_date` is earlier than
        today.
    """
    if due_date is None:
        return False
    if status_ == TaskStatus.DONE:
        return False
    return due_date < date.today()
