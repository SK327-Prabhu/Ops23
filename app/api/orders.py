"""Orders API router for Ops23."""

from typing import Any, Dict, List
from fastapi import APIRouter
from app.logger import logger

router = APIRouter(prefix="/api/orders", tags=["Orders"])

# Sample mock orders data
MOCK_ORDERS: List[Dict[str, Any]] = [
    {
        "id": "ord-5001",
        "order_number": "OPS-2026-001",
        "user_id": "usr-101",
        "amount": 149.99,
        "currency": "USD",
        "status": "completed",
        "items_count": 3,
        "created_at": "2026-09-20T09:12:00Z",
    },
    {
        "id": "ord-5002",
        "order_number": "OPS-2026-002",
        "user_id": "usr-102",
        "amount": 420.50,
        "currency": "USD",
        "status": "processing",
        "items_count": 5,
        "created_at": "2026-09-22T14:28:00Z",
    },
    {
        "id": "ord-5003",
        "order_number": "OPS-2026-003",
        "user_id": "usr-103",
        "amount": 89.00,
        "currency": "USD",
        "status": "completed",
        "items_count": 1,
        "created_at": "2026-09-25T11:05:00Z",
    },
    {
        "id": "ord-5004",
        "order_number": "OPS-2026-004",
        "user_id": "usr-104",
        "amount": 1250.00,
        "currency": "USD",
        "status": "pending_payment",
        "items_count": 8,
        "created_at": "2026-09-27T16:40:00Z",
    },
]


@router.get("", summary="List Orders", response_model=Dict[str, Any])
async def list_orders() -> Dict[str, Any]:
    """Retrieve list of customer orders."""
    logger.info("Retrieved orders list", extra={"total_orders": len(MOCK_ORDERS)})
    return {
        "orders": MOCK_ORDERS,
        "total": len(MOCK_ORDERS),
    }
