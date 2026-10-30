from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from stdevsec_api.services import market


def _account(client: TestClient, cash: float = 10_000.0) -> str:
    r = client.post("/api/v1/paper/accounts", json={"name": "Sim", "initial_cash": cash})
    assert r.status_code == 201, r.text
    return r.json()["id"]


def _order(client: TestClient, acc: str, side: str, qty: float, price: float):
    return client.post(
        f"/api/v1/paper/accounts/{acc}/orders",
        json={"symbol": "BTCUSDT", "side": side, "qty": qty, "price": price},
    )


def test_buy_then_sell_updates_cash_and_position(client: TestClient) -> None:
    acc = _account(client, 10_000.0)
    assert _order(client, acc, "buy", 0.1, 50_000.0).status_code == 201  # spend 5000

    detail = client.get(f"/api/v1/paper/accounts/{acc}").json()
    assert detail["cash"] == pytest.approx(5_000.0)
    assert detail["positions"][0]["qty"] == pytest.approx(0.1)
    assert detail["positions"][0]["avg_price"] == pytest.approx(50_000.0)

    assert _order(client, acc, "sell", 0.1, 60_000.0).status_code == 201  # gain 6000
    detail = client.get(f"/api/v1/paper/accounts/{acc}").json()
    assert detail["cash"] == pytest.approx(11_000.0)  # 5000 + 6000
    assert detail["positions"] == []  # flat -> position dropped


def test_average_price_on_second_buy(client: TestClient) -> None:
    acc = _account(client, 10_000.0)
    _order(client, acc, "buy", 1.0, 100.0)
    _order(client, acc, "buy", 1.0, 200.0)
    pos = client.get(f"/api/v1/paper/accounts/{acc}").json()["positions"][0]
    assert pos["qty"] == pytest.approx(2.0)
    assert pos["avg_price"] == pytest.approx(150.0)


def test_insufficient_funds_rejected(client: TestClient) -> None:
    acc = _account(client, 100.0)
    r = _order(client, acc, "buy", 1.0, 50_000.0)
    assert r.status_code == 422
    assert r.json()["error"]["code"] == "validation_error"


def test_oversell_rejected(client: TestClient) -> None:
    acc = _account(client, 10_000.0)
    _order(client, acc, "buy", 0.05, 50_000.0)
    r = _order(client, acc, "sell", 1.0, 50_000.0)
    assert r.status_code == 422


def test_orders_history_and_404(client: TestClient) -> None:
    acc = _account(client)
    _order(client, acc, "buy", 0.01, 50_000.0)
    page = client.get(f"/api/v1/paper/accounts/{acc}/orders").json()
    assert page["total"] == 1 and page["items"][0]["side"] == "buy"
    assert client.get("/api/v1/paper/accounts/nope").status_code == 404


def test_price_endpoint_uses_market(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(market, "fetch_price", lambda symbol: 12345.67)
    r = client.get("/api/v1/paper/price", params={"symbol": "btcusdt"})
    assert r.status_code == 200
    body = r.json()
    assert body == {"symbol": "BTCUSDT", "price": 12345.67}


def test_price_invalid_symbol(client: TestClient) -> None:
    r = client.get("/api/v1/paper/price", params={"symbol": "bad!!"})
    assert r.status_code == 422
