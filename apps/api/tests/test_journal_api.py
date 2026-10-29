from __future__ import annotations

from fastapi.testclient import TestClient

PNG = b"\x89PNG\r\n\x1a\n" + b"fake-image-bytes"


def _create(client: TestClient, **kw: object) -> dict:
    body = {"title": "Idea", "notes": "rompió resistencia", "tags": ["breakout", " "], **kw}
    r = client.post("/api/v1/journal/entries", json=body)
    assert r.status_code == 201, r.text
    return r.json()


def test_create_list_get_entry(client: TestClient) -> None:
    entry = _create(client)
    assert entry["title"] == "Idea"
    assert entry["tags"] == ["breakout"]  # blank tag stripped

    page = client.get("/api/v1/journal/entries").json()
    assert page["total"] == 1 and len(page["items"]) == 1

    detail = client.get(f"/api/v1/journal/entries/{entry['id']}").json()
    assert detail["images"] == []


def test_image_upload_and_serve(client: TestClient) -> None:
    entry_id = _create(client)["id"]
    up = client.post(
        f"/api/v1/journal/entries/{entry_id}/images",
        files={"file": ("shot.png", PNG, "image/png")},
    )
    assert up.status_code == 201, up.text
    image_id = up.json()["id"]

    got = client.get(f"/api/v1/journal/entries/{entry_id}/images/{image_id}")
    assert got.status_code == 200
    assert got.headers["content-type"].startswith("image/png")
    assert got.content == PNG

    detail = client.get(f"/api/v1/journal/entries/{entry_id}").json()
    assert len(detail["images"]) == 1 and detail["images"][0]["filename"] == "shot.png"


def test_non_image_rejected(client: TestClient) -> None:
    entry_id = _create(client)["id"]
    r = client.post(
        f"/api/v1/journal/entries/{entry_id}/images",
        files={"file": ("notes.txt", b"hello", "text/plain")},
    )
    assert r.status_code == 422
    assert r.json()["error"]["code"] == "validation_error"


def test_delete_entry_cascades(client: TestClient) -> None:
    entry_id = _create(client)["id"]
    client.post(
        f"/api/v1/journal/entries/{entry_id}/images",
        files={"file": ("s.png", PNG, "image/png")},
    )
    assert client.delete(f"/api/v1/journal/entries/{entry_id}").status_code == 204
    assert client.get(f"/api/v1/journal/entries/{entry_id}").status_code == 404


def test_missing_entry_404(client: TestClient) -> None:
    assert client.get("/api/v1/journal/entries/nope").status_code == 404
