"""API tests using FastAPI's TestClient (requires: pip install -r requirements-dev.txt)."""
import pytest

pytest.importorskip("fastapi")
pytest.importorskip("httpx")

from fastapi.testclient import TestClient  # noqa: E402

import app as app_module  # noqa: E402

client = TestClient(app_module.app)


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "healthy"
    assert body["knowledge_base_size"] > 0


def test_suggest_resolution_returns_timing_and_matches():
    r = client.post(
        "/api/suggest-resolution",
        json={"category": "Printer Issues", "priority": "Medium", "description": "Printer shows offline"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["similar_tickets"]
    assert body["timing"]["total_time_ms"] >= 0
    assert 0 <= body["confidence"] <= 1


@pytest.mark.parametrize(
    "payload",
    [
        {"category": "VPN Access", "priority": "High", "description": "   "},
        {"category": "VPN Access", "priority": "High", "description": "abc"},
        {"category": "", "priority": "High", "description": "VPN not working"},
        {"priority": "High", "description": "VPN not working"},
    ],
)
def test_invalid_requests_are_rejected(payload):
    assert client.post("/api/suggest-resolution", json=payload).status_code == 422


def test_categories_and_stats():
    cats = client.get("/api/categories").json()["categories"]
    assert "VPN Access" in cats
    stats = client.get("/api/stats").json()
    assert stats["total_tickets"] > 0


def test_feedback_is_recorded_in_metrics():
    r = client.post("/api/feedback/TKT0001", json={"feedback": "Worked", "helpful": True})
    assert r.status_code == 200
    assert client.get("/api/metrics").json()["feedback"]["helpful"] >= 1
    assert client.post("/api/feedback/TKT0001", json={}).status_code == 422


def test_reload_requires_admin_token(monkeypatch):
    monkeypatch.delenv("ADMIN_TOKEN", raising=False)
    assert client.post("/api/reload-knowledge-base").status_code == 403
    monkeypatch.setenv("ADMIN_TOKEN", "secret")
    assert client.post("/api/reload-knowledge-base").status_code == 401
    r = client.post("/api/reload-knowledge-base", headers={"X-Admin-Token": "secret"})
    assert r.status_code == 200
