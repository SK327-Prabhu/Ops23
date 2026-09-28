"""Simulation router for controlled failures and process crashes in Ops23."""

import os
import threading
import time
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from fastapi import APIRouter, Body
from app.config import settings
from app.logger import logger

router = APIRouter(prefix="/api/simulate", tags=["Simulation"])


class SimulatedApplicationError(RuntimeError):
    """Exception raised intentionally to simulate application failure."""

    pass


@router.post("/error", summary="Simulate Controlled Application Error")
async def simulate_error(
    payload: Optional[Dict[str, Any]] = Body(default=None),
) -> Dict[str, Any]:
    """Intentionally triggers a controlled application exception to verify

    logging and alerting pipelines.
    """
    error_message = (payload or {}).get(
        "message", "Simulated application failure: unexpected internal processing error"
    )
    error_code = (payload or {}).get("error_code", "SIMULATED_FAILURE_500")

    logger.error(
        f"Intentional application error triggered: {error_message}",
        extra={
            "simulation": True,
            "error_code": error_code,
            "simulated_error": error_message,
        },
    )

    raise SimulatedApplicationError(error_message)


@router.post("/crash", summary="Simulate Application Process Crash")
async def simulate_crash(
    payload: Optional[Dict[str, Any]] = Body(default=None),
) -> Dict[str, Any]:
    """Simulates an application process crash in a controlled manner for

    Datadog alerting and AWS SSM auto-remediation testing.
    """
    delay_seconds = float((payload or {}).get("delay_seconds", 0.5))

    logger.critical(
        "FATAL: Controlled process crash simulation initiated. Process exiting.",
        extra={
            "simulation": True,
            "crash_delay_seconds": delay_seconds,
            "exit_code": 1,
        },
    )

    def _terminate():
        time.sleep(delay_seconds)
        os._exit(1)

    # In automated testing or when TESTING=True, do not terminate the test runner
    if not settings.TESTING:
        threading.Thread(target=_terminate, daemon=True).start()

    return {
        "status": "crash_initiated",
        "message": f"Application crash initiated. Process will exit in {delay_seconds}s.",
        "service": settings.SERVICE_NAME,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
