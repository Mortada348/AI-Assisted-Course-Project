"""
Pydantic response models used by the health-check endpoint.
"""
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Schema returned by GET /health to indicate the API is running."""

    status: str = Field(
        ...,
        description="Current health status of the API.",
        json_schema_extra={"example": "ok"},
    )
    timestamp: str = Field(
        ...,
        description="UTC timestamp (ISO 8601) of when the health check ran.",
        json_schema_extra={"example": "2026-07-07T12:00:00.000000+00:00"},
    )
