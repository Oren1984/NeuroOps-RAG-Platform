# tests/smoke_test.py
# Smoke test for NeuroOps – RAG Platform API

"""
Minimal smoke test for NeuroOps – RAG Platform API
Tests basic endpoints without requiring pytest
"""

import sys
import requests
import json

BASE_URL = "http://127.0.0.1:8000"
API_KEY = "dev-test-key-12345"

def test_health():
    """Test /health endpoint"""
    print("Testing /health endpoint...")
    response = requests.get(f"{BASE_URL}/health")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.json()
    assert data["status"] == "ok", f"Expected status=ok, got {data.get('status')}"
    assert "app" in data, "Missing 'app' field in response"
    print("[OK] /health endpoint OK")
    return True

def test_ready():
    """Test /ready endpoint"""
    print("Testing /ready endpoint...")
    response = requests.get(f"{BASE_URL}/ready")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.json()
    assert "ready" in data, "Missing 'ready' field in response"
    assert "provider" in data, "Missing 'provider' field in response"
    print("[OK] /ready endpoint OK")
    return True

def test_ask_unauthorized():
    """Test /ask endpoint without API key (should fail)"""
    print("Testing /ask endpoint without API key...")
    response = requests.post(
        f"{BASE_URL}/ask",
        json={"question": "test"}
    )
    assert response.status_code == 401, f"Expected 401, got {response.status_code}"
    print("[OK] /ask endpoint correctly rejects unauthorized requests")
    return True

def test_ask_authorized():
    """Test /ask endpoint with valid API key"""
    print("Testing /ask endpoint with valid API key...")
    headers = {"X-API-Key": API_KEY}
    response = requests.post(
        f"{BASE_URL}/ask",
        json={"question": "What is RAG?"},
        headers=headers
    )
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.json()
    assert "answer" in data, "Missing 'answer' field in response"
    assert "provider" in data, "Missing 'provider' field in response"
    assert "sources" in data, "Missing 'sources' field in response"
    print("[OK] /ask endpoint OK with authorization")
    return True

def main():
    """Run all smoke tests"""
    print("=" * 60)
    print("NeuroOps – RAG Platform - Smoke Test Suite")
    print("=" * 60)
    
    tests = [
        test_health,
        test_ready,
        test_ask_unauthorized,
        test_ask_authorized,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"[FAIL] {test.__name__} FAILED: {e}")
            failed += 1
        print()
    
    print("=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60)
    
    if failed > 0:
        sys.exit(1)
    else:
        print("\n[OK] All smoke tests passed!")
        sys.exit(0)

if __name__ == "__main__":
    main()
