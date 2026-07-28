"""
API route module for health-check related endpoints.
"""
from datetime import datetime, timezone

from fastapi import APIRouter

from app.schemas.health import HealthResponse

# Router dedicated to health-check endpoints. It gets included into the
# main FastAPI app in app/main.py.
router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse, summary="Health check")
def get_health() -> HealthResponse:
    """Return a simple status payload confirming the API is up and running.

    Returns:
        HealthResponse: Contains a static "ok" status and the current UTC
        timestamp in ISO 8601 format.

    Example:
        GET /health
    """
    return HealthResponse(
        status="ok",
        timestamp=datetime.now(timezone.utc).isoformat(),
    )