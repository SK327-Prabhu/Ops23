"""Users API router for Ops23."""

from typing import Any, Dict, List
from fastapi import APIRouter
from app.logger import logger

router = APIRouter(prefix="/api/users", tags=["Users"])

# Sample mock users data
MOCK_USERS: List[Dict[str, Any]] = [
    {
        "id": "usr-101",
        "name": "Sarah Connor",
        "email": "sarah.connor@example.com",
        "role": "DevOps Engineer",
        "status": "active",
        "created_at": "2026-01-15T08:30:00Z",
    },
    {
        "id": "usr-102",
        "name": "Miles Dyson",
        "email": "m.dyson@example.com",
        "role": "Cloud Architect",
        "status": "active",
        "created_at": "2026-02-01T10:15:00Z",
    },
    {
        "id": "usr-103",
        "name": "John Connor",
        "email": "john.connor@example.com",
        "role": "Site Reliability Engineer",
        "status": "active",
        "created_at": "2026-03-10T14:45:00Z",
    },
    {
        "id": "usr-104",
        "name": "Kyle Reese",
        "email": "k.reese@example.com",
        "role": "Security Analyst",
        "status": "inactive",
        "created_at": "2026-04-05T12:00:00Z",
    },
]


@router.get("", summary="List Users", response_model=Dict[str, Any])
async def list_users() -> Dict[str, Any]:
    """Retrieve list of registered users."""
    logger.info("Retrieved users list", extra={"total_users": len(MOCK_USERS)})
    return {
        "users": MOCK_USERS,
        "total": len(MOCK_USERS),
    }
