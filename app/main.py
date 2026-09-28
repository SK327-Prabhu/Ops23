"""Main FastAPI application entrypoint for Ops23 API."""

import time
import uuid
from datetime import datetime, timezone
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from app.config import settings
from app.health import router as health_router
from app.api.users import router as users_router
from app.api.orders import router as orders_router
from app.api.simulate import router as simulate_router
from app.logger import endpoint_ctx, logger, request_id_ctx, setup_logging

# Initialize structured logging
setup_logging()

app = FastAPI(
    title=settings.APP_NAME,
    description="AIOps application layer for AWS EC2 monitoring, Datadog telemetry, and automated remediation.",
    version=settings.VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
)


@app.middleware("http")
async def correlation_and_logging_middleware(request: Request, call_next):
    """Correlate incoming requests with a unique Request-ID, capture metrics, and log lifecycle."""
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    token_req_id = request_id_ctx.set(request_id)
    token_endpoint = endpoint_ctx.set(request.url.path)

    start_time = time.perf_counter()
    logger.info(
        f"Incoming request: {request.method} {request.url.path}",
        extra={
            "http_method": request.method,
            "http_path": request.url.path,
        },
    )

    try:
        response = await call_next(request)
        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
        response.headers["X-Request-ID"] = request_id

        logger.info(
            f"Completed request: {request.method} {request.url.path} -> {response.status_code} ({duration_ms}ms)",
            extra={
                "http_method": request.method,
                "http_status_code": response.status_code,
                "duration_ms": duration_ms,
            },
        )
        return response
    finally:
        request_id_ctx.reset(token_req_id)
        endpoint_ctx.reset(token_endpoint)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Centralized handler for HTTPExceptions."""
    req_id = request_id_ctx.get() or request.headers.get("X-Request-ID", "unknown")
    if exc.status_code >= 500:
        logger.error(
            f"HTTP {exc.status_code} server error: {exc.detail}",
            extra={"status_code": exc.status_code, "request_id": req_id, "endpoint": request.url.path},
        )
    else:
        logger.warning(
            f"HTTP {exc.status_code} client error: {exc.detail}",
            extra={"status_code": exc.status_code, "request_id": req_id, "endpoint": request.url.path},
        )
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": "HTTPException",
            "message": exc.detail,
            "status_code": exc.status_code,
            "request_id": req_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
        headers={"X-Request-ID": req_id},
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Centralized exception handler ensuring all unhandled errors emit structured ERROR logs."""
    req_id = request_id_ctx.get() or request.headers.get("X-Request-ID", "unknown")
    logger.error(
        f"Unhandled application exception: {type(exc).__name__}: {str(exc)}",
        exc_info=exc,
        extra={
            "endpoint": request.url.path,
            "request_id": req_id,
            "error_type": type(exc).__name__,
        },
    )
    return JSONResponse(
        status_code=500,
        content={
            "error": "InternalServerError",
            "message": "An application error occurred. Incident logged for operational analysis.",
            "detail": str(exc),
            "request_id": req_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
        headers={"X-Request-ID": req_id},
    )


# Mount application routers
app.include_router(health_router)
app.include_router(users_router)
app.include_router(orders_router)
app.include_router(simulate_router)


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint welcoming clients and directing to documentation."""
    return {
        "message": f"Welcome to {settings.APP_NAME} - {settings.PROJECT_TITLE}",
        "service": settings.SERVICE_NAME,
        "app_name": settings.APP_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "docs": "/docs",
        "health": "/health",
        "endpoints": {
            "health": "/health",
            "users": "/api/users",
            "orders": "/api/orders",
            "simulate_error": "/api/simulate/error",
            "simulate_crash": "/api/simulate/crash",
        },
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
    )
