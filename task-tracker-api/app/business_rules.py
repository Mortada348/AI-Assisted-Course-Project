from fastapi import HTTPException, status
from datetime import date

from app.models import TaskStatus

VALID_TRANSITIONS: frozenset[tuple[TaskStatus, TaskStatus]] = frozenset({
    (TaskStatus.TODO, TaskStatus.IN_PROGRESS),
    (TaskStatus.IN_PROGRESS, TaskStatus.DONE),
    (TaskStatus.DONE, TaskStatus.IN_PROGRESS),
})


def validate_status_transition(current: TaskStatus, new: TaskStatus) -> None:
    if (current, new) not in VALID_TRANSITIONS:
        allowed = sorted({f"{f.value}->{t.value}" for f, t in VALID_TRANSITIONS})
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid status transition from {current.value} to {new.value}. Allowed transitions: {allowed}",
        )


def validate_tag(tag: str) -> str:
    stripped = tag.strip()
    if not stripped:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="tag cannot be blank",
        )
    return stripped


def validate_no_duplicate_tags(tags: list[str]) -> list[str]:
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
    normalized_target = tag_to_remove.strip().casefold()
    if not any(tag.casefold() == normalized_target for tag in existing_tags):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Tag '{tag_to_remove}' does not exist and cannot be removed",
        )


def is_task_overdue(due_date: date | None, status_: TaskStatus) -> bool:
    if due_date is None:
        return False
    if status_ == TaskStatus.DONE:
        return False
    return due_date < date.today()
