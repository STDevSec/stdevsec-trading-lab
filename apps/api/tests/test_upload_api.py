from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from helpers import csv_bytes

from stdevsec_api.config import get_settings


def _upload(client: TestClient, data: bytes, **form: str):
    fields = {"name": "AAPL daily", "timeframe": "1d", "symbol": "AAPL", **form}
    return client.post(
        "/api/v1/datasets/upload", data=fields, files={"file": ("d.csv", data, "text/csv")}
    )


def test_upload_csv_creates_dataset_and_backtests(client: TestClient) -> None:
    r = _upload(client, csv_bytes(rows=120, seed=3))
    assert r.status_code == 201, r.text
    ds = r.json()
    assert ds["symbol"] == "AAPL"

    detail = client.get(f"/api/v1/datasets/{ds['id']}").json()
    assert detail["versions"][0]["n_rows"] == 120
    assert detail["versions"][0]["is_valid"] is True

    # The uploaded dataset is usable end-to-end.
    run = client.post(
        "/api/v1/backtests",
        json={"dataset_id": ds["id"], "strategy": "buy_and_hold"},
    )
    assert run.status_code == 201, run.text


def test_upload_missing_columns_rejected(client: TestClient) -> None:
    bad = b"timestamp,open,close\n2024-01-01T00:00:00+00:00,100,101\n"
    r = _upload(client, bad)
    assert r.status_code == 422
    err = r.json()["error"]
    assert err["code"] == "validation_error"
    assert "high" in err["details"]["missing"]


def test_upload_empty_csv_rejected(client: TestClient) -> None:
    r = _upload(client, b"timestamp,open,high,low,close,volume\n")
    assert r.status_code == 422


def test_upload_too_large_rejected(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(get_settings(), "max_upload_bytes", 10)
    r = _upload(client, csv_bytes(rows=30))
    assert r.status_code == 413
    assert r.json()["error"]["code"] == "payload_too_large"
