"""Tests for /health and root endpoints."""

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_endpoint():
    """Verify that /health returns HTTP 200 with expected healthy payload structure."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "Ops23"
    assert "version" in data
    assert "environment" in data
    assert "timestamp" in data


def test_root_endpoint():
    """Verify that root endpoint returns HTTP 200 and basic metadata."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert data["health"] == "/health"
