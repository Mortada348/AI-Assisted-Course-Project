from datetime import date, datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, field_validator


class TaskStatus(str, Enum):
    TODO = "ToDo"
    IN_PROGRESS = "InProgress"
    DONE = "Done"


class TaskPriority(str, Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"


class TaskCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str
    description: Optional[str] = ""
    status: TaskStatus = TaskStatus.TODO
    priority: TaskPriority = TaskPriority.MEDIUM
    assignee: Optional[str] = None
    due_date: Optional[date] = None

    @field_validator("title")
    @classmethod
    def validate_title(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("title cannot be blank")
        if len(stripped) > 200:
            raise ValueError("title must be at most 200 characters")
        return stripped

    @field_validator("due_date", mode="before")
    @classmethod
    def validate_due_date(cls, v):
        if v is None or v == "":
            return None
        if isinstance(v, datetime):
            now = datetime.now(tz=v.tzinfo) if v.tzinfo else datetime.now()
            if v <= now:
                raise ValueError("due_date must be a future date")
            return v.date()
        if isinstance(v, date):
            if v <= date.today():
                raise ValueError("due_date must be a future date")
            return v
        try:
            parsed = date.fromisoformat(str(v))
        except ValueError:
            raise ValueError("due_date must be a valid date in YYYY-MM-DD format")
        if parsed <= date.today():
            raise ValueError("due_date must be a future date")
        return parsed


class TaskUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[TaskStatus] = None
    priority: Optional[TaskPriority] = None
    assignee: Optional[str] = None
    due_date: Optional[date] = None

    @field_validator("title")
    @classmethod
    def validate_title(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        stripped = v.strip()
        if not stripped:
            raise ValueError("title cannot be blank")
        if len(stripped) > 200:
            raise ValueError("title must be at most 200 characters")
        return stripped

    @field_validator("due_date", mode="before")
    @classmethod
    def validate_due_date(cls, v):
        if v is None or v == "":
            return None
        if isinstance(v, datetime):
            now = datetime.now(tz=v.tzinfo) if v.tzinfo else datetime.now()
            if v <= now:
                raise ValueError("due_date must be a future date")
            return v.date()
        if isinstance(v, date):
            if v <= date.today():
                raise ValueError("due_date must be a future date")
            return v
        try:
            parsed = date.fromisoformat(str(v))
        except ValueError:
            raise ValueError("due_date must be a valid date in YYYY-MM-DD format")
        if parsed <= date.today():
            raise ValueError("due_date must be a future date")
        return parsed


class TaskResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    title: str
    description: str
    status: TaskStatus
    priority: TaskPriority
    assignee: Optional[str]
    due_date: Optional[date] = None
    is_overdue: bool = False
    created_at: datetime
    updated_at: datetime
