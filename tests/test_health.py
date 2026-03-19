# tests/test_health.py
# Test health and ready endpoints

from fastapi.testclient import TestClient
from src.main import app
import os

client = TestClient(app)

## Test Cases
def test_health():
    """Test the health endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "app" in data

# Ready Endpoint Test
def test_ready():
    """Test the ready endpoint"""
    response = client.get("/ready")
    assert response.status_code == 200
    data = response.json()
    assert "ready" in data
    assert "provider" in data

# Ask Endpoint Tests
def test_ask_unauthorized():
    """Test ask endpoint without API key"""
    response = client.post("/ask", json={"question": "test"})
    assert response.status_code == 401

# Ask Endpoint Tests with Authorization
def test_ask_authorized():
    """Test ask endpoint with valid API key"""
    headers = {"X-API-Key": os.getenv("RAG_API_KEY", "ci-test-key")}
    response = client.post(
        "/ask",
        json={"question": "What is RAG?"},
        headers=headers
    )
    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert "provider" in data
    assert "sources" in data
