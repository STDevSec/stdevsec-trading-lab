from __future__ import annotations

from fastapi.testclient import TestClient
from helpers import dataset_payload


def _make_dataset(client: TestClient, **kw: object) -> str:
    return client.post("/api/v1/datasets", json=dataset_payload(**kw)).json()["id"]


def test_strategy_catalog(client: TestClient) -> None:
    r = client.get("/api/v1/strategies")
    assert r.status_code == 200
    names = {s["name"] for s in r.json()}
    assert {"buy_and_hold", "sma_crossover"} <= names


def test_run_backtest_end_to_end(client: TestClient) -> None:
    dataset_id = _make_dataset(client, rows=120, seed=42)
    r = client.post(
        "/api/v1/backtests",
        json={"dataset_id": dataset_id, "strategy": "buy_and_hold", "initial_capital": 1000.0},
    )
    assert r.status_code == 201, r.text
    run = r.json()
    assert run["status"] == "completed"
    assert run["strategy_name"] == "buy_and_hold"
    assert "total_return" in run
    assert run["metrics"]["n_trades"] >= 0
    run_id = run["id"]

    assert client.get(f"/api/v1/backtests/{run_id}").status_code == 200

    metrics = client.get(f"/api/v1/backtests/{run_id}/metrics")
    assert metrics.status_code == 200
    assert "max_drawdown" in metrics.json()

    trades = client.get(f"/api/v1/backtests/{run_id}/trades")
    assert trades.status_code == 200
    assert "items" in trades.json()

    equity = client.get(f"/api/v1/backtests/{run_id}/equity")
    assert equity.status_code == 200
    curve = equity.json()
    assert len(curve) == 120  # one point per bar
    assert curve[0]["timestamp"] < curve[-1]["timestamp"]  # ordered
    assert all("equity" in p for p in curve)


def test_equity_unknown_run_404(client: TestClient) -> None:
    assert client.get("/api/v1/backtests/missing/equity").status_code == 404


def test_sma_backtest_persists_trades(client: TestClient) -> None:
    dataset_id = _make_dataset(client, rows=200, seed=7)
    r = client.post(
        "/api/v1/backtests",
        json={
            "dataset_id": dataset_id,
            "strategy": "sma_crossover",
            "params": {"fast": 5, "slow": 20},
            "commission_bps": 5.0,
        },
    )
    assert r.status_code == 201, r.text
    run_id = r.json()["id"]
    trades = client.get(f"/api/v1/backtests/{run_id}/trades").json()
    assert isinstance(trades["total"], int)
    assert trades["total"] >= 0
    assert len(trades["items"]) == min(trades["total"], trades["limit"])


def test_unknown_strategy_rejected(client: TestClient) -> None:
    dataset_id = _make_dataset(client)
    r = client.post(
        "/api/v1/backtests",
        json={"dataset_id": dataset_id, "strategy": "nope"},
    )
    assert r.status_code == 422
    assert r.json()["error"]["code"] == "validation_error"


def test_backtest_unknown_dataset_404(client: TestClient) -> None:
    r = client.post(
        "/api/v1/backtests",
        json={"dataset_id": "missing", "strategy": "buy_and_hold"},
    )
    assert r.status_code == 404
