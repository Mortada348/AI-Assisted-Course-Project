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
    tags: list[str] = []
    due_date: Optional[date] = None

    @field_validator("title")
    @classmethod
    def validate_title(cls, v: str) -> str:
        """Strip whitespace and enforce title constraints.

        Args:
            v: The raw title string.

        Returns:
            str: The stripped title.

        Raises:
            ValueError: If the stripped title is empty, or longer than
                200 characters.
        """
        stripped = v.strip()
        if not stripped:
            raise ValueError("title cannot be blank")
        if len(stripped) > 200:
            raise ValueError("title must be at most 200 characters")
        return stripped

    @field_validator("tags", mode="before")
    @classmethod
    def validate_tags(cls, v):
        """Normalize and deduplicate the tags list before other validation.

        Args:
            v: The raw tags value from the input payload.

        Returns:
            list[str]: An empty list if `v` is None; otherwise, stripped
            tags with case-insensitive duplicates removed (first
            occurrence kept).

        Raises:
            TypeError: If `v` is not a list, or contains a non-string
                element.
            ValueError: If a tag is empty or blank after stripping.
        """
        if v is None:
            return []
        if not isinstance(v, list):
            raise TypeError("tags must be a list of strings")
        cleaned_tags: list[str] = []
        seen: dict[str, bool] = {}
        for tag in v:
            if not isinstance(tag, str):
                raise TypeError("tags must be a list of strings")
            stripped = tag.strip()
            if not stripped:
                raise ValueError("tags cannot contain empty or blank values")
            key = stripped.casefold()
            if key in seen:
                continue
            seen[key] = True
            cleaned_tags.append(stripped)
        return cleaned_tags

    @field_validator("due_date", mode="before")
    @classmethod
    def validate_due_date(cls, v):
        """Parse and validate that a due date is set in the future.

        Args:
            v: The raw due_date value — may be None, an empty string, a
                `datetime`, a `date`, or a string in ISO format.

        Returns:
            Optional[date]: None if `v` is None or an empty string;
            otherwise the parsed `date`.

        Raises:
            ValueError: If `v` is a `datetime`/`date` that is not strictly
                after the current moment/today, if the string cannot be
                parsed as an ISO date, or if the parsed date is not
                strictly after today.
        """
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
    tags: list[str] = []
    due_date: Optional[date] = None
    add_tags: Optional[list[str]] = None
    remove_tags: Optional[list[str]] = None

    @field_validator("title")
    @classmethod
    def validate_title(cls, v: Optional[str]) -> Optional[str]:
        """Strip whitespace and enforce title constraints, allowing unset values.

        Args:
            v: The raw title value, or None if not provided.

        Returns:
            Optional[str]: None if `v` is None; otherwise the stripped
            title.

        Raises:
            ValueError: If the stripped title is empty, or longer than
                200 characters.
        """
        if v is None:
            return v
        stripped = v.strip()
        if not stripped:
            raise ValueError("title cannot be blank")
        if len(stripped) > 200:
            raise ValueError("title must be at most 200 characters")
        return stripped

    @field_validator("tags", mode="before")
    @classmethod
    def validate_tags(cls, v):
        """Normalize and deduplicate the tags list before other validation.

        Args:
            v: The raw tags value from the input payload.

        Returns:
            list[str]: An empty list if `v` is None; otherwise, stripped
            tags with case-insensitive duplicates removed (first
            occurrence kept).

        Raises:
            TypeError: If `v` is not a list, or contains a non-string
                element.
            ValueError: If a tag is empty or blank after stripping.
        """
        if v is None:
            return []
        if not isinstance(v, list):
            raise TypeError("tags must be a list of strings")
        cleaned_tags: list[str] = []
        seen: dict[str, bool] = {}
        for tag in v:
            if not isinstance(tag, str):
                raise TypeError("tags must be a list of strings")
            stripped = tag.strip()
            if not stripped:
                raise ValueError("tags cannot contain empty or blank values")
            key = stripped.casefold()
            if key in seen:
                continue
            seen[key] = True
            cleaned_tags.append(stripped)
        return cleaned_tags

    @field_validator("due_date", mode="before")
    @classmethod
    def validate_due_date(cls, v):
        """Parse and validate that a due date is set in the future.

        Args:
            v: The raw due_date value — may be None, an empty string, a
                `datetime`, a `date`, or a string in ISO format.

        Returns:
            Optional[date]: None if `v` is None or an empty string;
            otherwise the parsed `date`.

        Raises:
            ValueError: If `v` is a `datetime`/`date` that is not strictly
                after the current moment/today, if the string cannot be
                parsed as an ISO date, or if the parsed date is not
                strictly after today.
        """
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

    @field_validator("add_tags", mode="before")
    @classmethod
    def validate_add_tags(cls, v):
        """Normalize and deduplicate tags to add, if provided.

        Args:
            v: The raw add_tags value, or None if not provided.

        Returns:
            Optional[list[str]]: None if `v` is None; otherwise stripped
            tags with case-insensitive duplicates removed (first
            occurrence kept).

        Raises:
            TypeError: If `v` is not a list, or contains a non-string
                element.
            ValueError: If a tag is empty or blank after stripping.
        """
        if v is None:
            return None
        if not isinstance(v, list):
            raise TypeError("add_tags must be a list of strings")
        cleaned_tags: list[str] = []
        seen: dict[str, bool] = {}
        for tag in v:
            if not isinstance(tag, str):
                raise TypeError("add_tags must be a list of strings")
            stripped = tag.strip()
            if not stripped:
                raise ValueError("add_tags cannot contain empty or blank values")
            key = stripped.casefold()
            if key in seen:
                continue
            seen[key] = True
            cleaned_tags.append(stripped)
        return cleaned_tags

    @field_validator("remove_tags", mode="before")
    @classmethod
    def validate_remove_tags(cls, v):
        """Normalize and deduplicate tags to remove, if provided.

        Args:
            v: The raw remove_tags value, or None if not provided.

        Returns:
            Optional[list[str]]: None if `v` is None; otherwise stripped
            tags with case-insensitive duplicates removed (first
            occurrence kept).

        Raises:
            TypeError: If `v` is not a list, or contains a non-string
                element.
            ValueError: If a tag is empty or blank after stripping.
        """
        if v is None:
            return None
        if not isinstance(v, list):
            raise TypeError("remove_tags must be a list of strings")
        cleaned_tags: list[str] = []
        seen: dict[str, bool] = {}
        for tag in v:
            if not isinstance(tag, str):
                raise TypeError("remove_tags must be a list of strings")
            stripped = tag.strip()
            if not stripped:
                raise ValueError("remove_tags cannot contain empty or blank values")
            key = stripped.casefold()
            if key in seen:
                continue
            seen[key] = True
            cleaned_tags.append(stripped)
        return cleaned_tags


class TaskResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    title: str
    description: str
    status: TaskStatus
    priority: TaskPriority
    assignee: Optional[str]
    tags: list[str] = []
    due_date: Optional[date] = None
    is_overdue: bool = False
    created_at: datetime
    updated_at: datetime
