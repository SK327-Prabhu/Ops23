"""Health check endpoints for Ops23 service."""

from datetime import datetime, timezone
from typing import Any, Dict
from fastapi import APIRouter
from app.config import settings

router = APIRouter(tags=["Health"])


@router.get("/health", summary="Health Check", response_model=Dict[str, Any])
async def health_check() -> Dict[str, Any]:
    """Return minimal health status indicating service operational status."""
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
