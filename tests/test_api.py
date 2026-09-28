"""Tests for Phase 1 endpoints: users, orders, simulations, and correlation."""

import pytest
from fastapi.testclient import TestClient
from app.config import settings
from app.main import app
from app.logger import StructuredJsonFormatter
import logging
import json

# Ensure test mode is active so crash simulations do not exit test runner
settings.TESTING = True

client = TestClient(app, raise_server_exceptions=False)


def test_root_endpoint_details():
    """Verify GET / returns complete service info and endpoint registry."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert data["service"] == "Ops23"
    assert data["app_name"] == "Ops23 API"
    assert "endpoints" in data
    assert data["endpoints"]["users"] == "/api/users"
    assert data["endpoints"]["orders"] == "/api/orders"
    assert data["endpoints"]["simulate_error"] == "/api/simulate/error"
    assert data["endpoints"]["simulate_crash"] == "/api/simulate/crash"


def test_get_users():
    """Verify GET /api/users returns a list of mock users."""
    response = client.get("/api/users")
    assert response.status_code == 200
    data = response.json()
    assert "users" in data
    assert "total" in data
    assert data["total"] > 0
    assert len(data["users"]) == data["total"]

    first_user = data["users"][0]
    assert "id" in first_user
    assert "name" in first_user
    assert "email" in first_user
    assert "role" in first_user
    assert "status" in first_user


def test_get_orders():
    """Verify GET /api/orders returns a list of mock orders."""
    response = client.get("/api/orders")
    assert response.status_code == 200
    data = response.json()
    assert "orders" in data
    assert "total" in data
    assert data["total"] > 0
    assert len(data["orders"]) == data["total"]

    first_order = data["orders"][0]
    assert "id" in first_order
    assert "order_number" in first_order
    assert "amount" in first_order
    assert "currency" in first_order
    assert "status" in first_order


def test_simulate_error():
    """Verify POST /api/simulate/error triggers centralized error handling and returns 500."""
    payload = {"message": "Custom simulated failure for AIOps triage test"}
    response = client.post("/api/simulate/error", json=payload)
    assert response.status_code == 500
    data = response.json()
    assert data["error"] == "InternalServerError"
    assert "Custom simulated failure" in data["detail"]
    assert "request_id" in data
    assert "timestamp" in data
    assert "X-Request-ID" in response.headers


def test_simulate_crash():
    """Verify POST /api/simulate/crash initiates controlled crash sequence in test mode."""
    response = client.post("/api/simulate/crash", json={"delay_seconds": 0.1})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "crash_initiated"
    assert data["service"] == "Ops23"
    assert "timestamp" in data


def test_request_id_correlation_header():
    """Verify that custom X-Request-ID headers are honored and returned."""
    custom_id = "test-corr-id-9999"
    response = client.get("/health", headers={"X-Request-ID": custom_id})
    assert response.status_code == 200
    assert response.headers.get("X-Request-ID") == custom_id


def test_structured_logger_formatting():
    """Verify that StructuredJsonFormatter outputs valid JSON and redacts sensitive keys."""
    formatter = StructuredJsonFormatter()
    record = logging.LogRecord(
        name="test_logger",
        level=logging.ERROR,
        pathname="test_file.py",
        lineno=10,
        msg="Testing secret token leak",
        args=(),
        exc_info=None,
    )
    record.endpoint = "/api/test"
    record.request_id = "req-123"
    setattr(record, "password", "my_super_secret_password")
    setattr(record, "api_key", "secret-key-123")

    formatted = formatter.format(record)
    log_obj = json.loads(formatted)

    assert log_obj["level"] == "ERROR"
    assert log_obj["service"] == "Ops23"
    assert log_obj["endpoint"] == "/api/test"
    assert log_obj["request_id"] == "req-123"
    assert log_obj["password"] == "[REDACTED]"
    assert log_obj["api_key"] == "[REDACTED]"
