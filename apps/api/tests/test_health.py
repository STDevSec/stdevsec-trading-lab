from __future__ import annotations

from fastapi.testclient import TestClient

from stdevsec_api.main import app

client = TestClient(app)


def test_health_ok() -> None:
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_ready_ok() -> None:
    r = client.get("/ready")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ready"
    assert body["checks"]["quant_engine"] == "ok"


def test_request_id_header_present() -> None:
    r = client.get("/health")
    assert r.headers.get("X-Request-ID")


def test_request_id_echoed_when_supplied() -> None:
    r = client.get("/health", headers={"X-Request-ID": "abc-123"})
    assert r.headers["X-Request-ID"] == "abc-123"
