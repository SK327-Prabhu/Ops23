"""Lightweight structured JSON logging using Python standard library."""

import json
import logging
import sys
import traceback
from contextvars import ContextVar
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from app.config import settings

# Context variables for request-scoped correlation
request_id_ctx: ContextVar[str] = ContextVar("request_id", default="")
endpoint_ctx: ContextVar[str] = ContextVar("endpoint", default="")

# Standard LogRecord attribute names to ignore when extracting custom extra fields
_STANDARD_RECORD_ATTRS = {
    "name",
    "msg",
    "args",
    "levelname",
    "levelno",
    "pathname",
    "filename",
    "module",
    "exc_info",
    "exc_text",
    "stack_info",
    "lineno",
    "funcName",
    "created",
    "msecs",
    "relativeCreated",
    "thread",
    "threadName",
    "processName",
    "process",
    "message",
    "asctime",
}

# Sensitive keys to redact
_SENSITIVE_KEYS = {
    "password",
    "token",
    "secret",
    "authorization",
    "api_key",
    "access_token",
    "private_key",
    "credit_card",
}


def _redact_sensitive_data(data: Any) -> Any:
    """Recursively redact sensitive field values from logged structures."""
    if isinstance(data, dict):
        redacted = {}
        for k, v in data.items():
            if any(s in str(k).lower() for s in _SENSITIVE_KEYS):
                redacted[k] = "[REDACTED]"
            else:
                redacted[k] = _redact_sensitive_data(v)
        return redacted
    elif isinstance(data, list):
        return [_redact_sensitive_data(item) for item in data]
    return data


class StructuredJsonFormatter(logging.Formatter):
    """Formats log records as single-line JSON objects optimized for Datadog log parsing."""

    def format(self, record: logging.LogRecord) -> str:
        # Base structured fields
        log_payload: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "service": settings.SERVICE_NAME,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Request ID correlation
        req_id = getattr(record, "request_id", None) or request_id_ctx.get()
        if req_id:
            log_payload["request_id"] = req_id

        # Endpoint correlation
        ep = getattr(record, "endpoint", None) or endpoint_ctx.get()
        if ep:
            log_payload["endpoint"] = ep

        # Error / Exception details
        if record.exc_info:
            exc_type, exc_val, exc_tb = record.exc_info
            log_payload["error"] = {
                "kind": exc_type.__name__ if exc_type else "Exception",
                "message": str(exc_val) if exc_val else "",
                "stack": "".join(traceback.format_exception(exc_type, exc_val, exc_tb)),
            }

        # Extract custom extra attributes
        for key, value in record.__dict__.items():
            if key not in _STANDARD_RECORD_ATTRS and key not in log_payload:
                log_payload[key] = _redact_sensitive_data(value)

        # Redact any sensitive content inside the payload
        sanitized = _redact_sensitive_data(log_payload)

        try:
            return json.dumps(sanitized, default=str)
        except Exception:
            # Fallback if serialization fails
            return json.dumps({
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "level": record.levelname,
                "service": settings.SERVICE_NAME,
                "message": record.getMessage(),
            })


def setup_logging(level: Optional[str] = None) -> logging.Logger:
    """Configure structured JSON logging for the application."""
    log_level_name = level or settings.LOG_LEVEL
    log_level = getattr(logging, log_level_name.upper(), logging.INFO)

    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Remove existing stream handlers to prevent duplicates
    for handler in list(root_logger.handlers):
        root_logger.removeHandler(handler)

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(log_level)
    handler.setFormatter(StructuredJsonFormatter())
    root_logger.addHandler(handler)

    app_logger = logging.getLogger("ops23")
    app_logger.setLevel(log_level)
    return app_logger


logger = logging.getLogger("ops23")
