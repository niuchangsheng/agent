import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

def test_health_check_active():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "active"}

def test_unknown_route_returns_404():
    response = client.get("/api/v1/dummy")
    assert response.status_code == 404
