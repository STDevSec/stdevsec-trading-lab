from __future__ import annotations

from fastapi.testclient import TestClient
from helpers import dataset_payload


def test_create_and_get_dataset(client: TestClient) -> None:
    r = client.post("/api/v1/datasets", json=dataset_payload(rows=50))
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["name"] == "Test"
    dataset_id = body["id"]

    got = client.get(f"/api/v1/datasets/{dataset_id}")
    assert got.status_code == 200
    detail = got.json()
    assert detail["versions"][0]["version"] == 1
    assert detail["versions"][0]["n_rows"] == 50
    assert detail["versions"][0]["is_valid"] is True


def test_list_datasets_paginated(client: TestClient) -> None:
    for i in range(3):
        client.post("/api/v1/datasets", json=dataset_payload(name=f"DS{i}", seed=i + 1))
    r = client.get("/api/v1/datasets", params={"limit": 2, "offset": 0})
    assert r.status_code == 200
    page = r.json()
    assert page["total"] == 3
    assert len(page["items"]) == 2
    assert page["limit"] == 2


def test_validate_endpoint(client: TestClient) -> None:
    dataset_id = client.post("/api/v1/datasets", json=dataset_payload()).json()["id"]
    r = client.post(f"/api/v1/datasets/{dataset_id}/validate")
    assert r.status_code == 200
    assert r.json()["is_valid"] is True


def test_invalid_dataset_rejected_with_report(client: TestClient) -> None:
    payload = dataset_payload(rows=10)
    # Break high/low consistency on one candle (passes field checks, fails OHLCV).
    payload["candles"][2]["high"] = payload["candles"][2]["low"] - 1.0
    r = client.post("/api/v1/datasets", json=payload)
    assert r.status_code == 422
    err = r.json()["error"]
    assert err["code"] == "validation_error"
    codes = {issue["code"] for issue in err["details"]["issues"]}
    assert "high_low_inconsistent" in codes


def test_missing_dataset_returns_404(client: TestClient) -> None:
    r = client.get("/api/v1/datasets/does-not-exist")
    assert r.status_code == 404
    assert r.json()["error"]["code"] == "not_found"


def test_ohlcv_with_indicators(client: TestClient) -> None:
    dataset_id = client.post("/api/v1/datasets", json=dataset_payload(rows=60)).json()["id"]
    r = client.get(f"/api/v1/datasets/{dataset_id}/ohlcv")
    assert r.status_code == 200
    body = r.json()
    assert len(body["candles"]) == 60
    assert body["candles"][0]["time"] < body["candles"][-1]["time"]  # unix seconds, ordered
    ind = body["indicators"]
    for key in ("sma20", "ema20", "bb_upper", "rsi14", "macd", "macd_hist"):
        assert len(ind[key]) == 60  # index-aligned with candles
    assert ind["sma20"][0] is None  # warm-up serialized as null, not NaN
    # RSI stays within bounds where defined.
    rsi_vals = [v for v in ind["rsi14"] if v is not None]
    assert rsi_vals and all(0 <= v <= 100 for v in rsi_vals)
