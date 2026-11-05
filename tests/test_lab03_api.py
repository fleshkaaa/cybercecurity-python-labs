import sqlite3
from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from labs.lab03 import database, seed
from labs.lab03.main import app


@pytest.fixture
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
    monkeypatch.setattr(database, "DATABASE_PATH", tmp_path / "test.sqlite3")
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def seeded(client: TestClient) -> TestClient:
    assert seed.run() == 0
    return client


def count(client: TestClient) -> int:
    return len(client.get("/records", params={"limit": 100}).json())


def new_record(code: str = "V06-99", category_id: int = 1, **extra: object) -> dict:
    body = {
        "code": code,
        "title": "Тестовий запис",
        "category_id": category_id,
        "value": 7,
        "status": "new",
    }
    return body | extra


def test_seed_and_repeat(client: TestClient, capsys: pytest.CaptureFixture) -> None:
    assert seed.run() == 0
    assert seed.run() == 0
    assert "пропущено" in capsys.readouterr().out
    assert len(client.get("/categories").json()) == 3
    assert count(client) == 8


def test_service_routes(seeded: TestClient) -> None:
    assert seeded.get("/ping").json() == {"status": "ok"}
    assert seeded.get("/student").json()["variant_number"] == 6
    names = [c["name"] for c in seeded.get("/categories").json()]
    assert names == ["phishing", "malicious_attachment", "spam"]


def test_crud_cycle(seeded: TestClient) -> None:
    created = seeded.post("/records", json=new_record())
    assert created.status_code == 201
    body = created.json()
    assert body["category_name"] == "phishing"
    url = f"/records/{body['id']}"
    assert seeded.get(url).status_code == 200
    replaced = seeded.put(url, json=new_record(status="done", value=3))
    assert replaced.status_code == 200
    assert replaced.json()["status"] == "done"
    assert replaced.json()["id"] == body["id"]
    assert seeded.delete(url).status_code == 204
    assert seeded.get(url).status_code == 404


def test_filters_and_paging(seeded: TestClient) -> None:
    rows = seeded.get("/records", params={"category_id": 1, "status": "new"}).json()
    assert [r["code"] for r in rows] == ["V06-01", "V06-04"]
    rows = seeded.get("/records", params={"min_value": 30}).json()
    assert [r["value"] for r in rows] == [30, 45]
    page = seeded.get("/records", params={"limit": 2, "offset": 2}).json()
    assert [r["id"] for r in page] == [3, 4]
    assert seeded.get("/records", params={"category_id": 99}).json() == []
    assert seeded.get("/records", params={"q": "пошти 0"}).json() != []
    assert seeded.get("/records", params={"q": "ПОШТИ"}).json() == []


@pytest.mark.parametrize(
    "patch",
    [
        {"value": -1},
        {"value": 1.5},
        {"value": "5"},
        {"value": True},
        {"title": "   "},
        {"status": "unknown"},
        {"category_id": 0},
        {"extra": 1},
    ],
)
def test_invalid_body_422(seeded: TestClient, patch: dict) -> None:
    response = seeded.post("/records", json=new_record() | patch)
    assert response.status_code == 422
    assert count(seeded) == 8


@pytest.mark.parametrize(
    "params", [{"limit": 0}, {"limit": 101}, {"offset": -1}, {"min_value": -1}]
)
def test_invalid_query_422(seeded: TestClient, params: dict) -> None:
    assert seeded.get("/records", params=params).status_code == 422


def test_not_found(seeded: TestClient) -> None:
    assert seeded.get("/records/999").status_code == 404
    assert seeded.get("/records/0").status_code == 422
    assert seeded.post("/records", json=new_record(category_id=99)).status_code == 404
    assert seeded.put("/records/999", json=new_record()).status_code == 404
    assert seeded.delete("/categories/99").status_code == 404


def test_conflicts(seeded: TestClient) -> None:
    assert seeded.post("/records", json=new_record(code="V06-01")).status_code == 409
    assert seeded.post("/categories", json={"name": "spam"}).status_code == 409
    assert seeded.delete("/categories/1").status_code == 409
    assert count(seeded) == 8


def test_delete_empty_category(seeded: TestClient) -> None:
    created = seeded.post("/categories", json={"name": "other"})
    assert created.status_code == 201
    assert seeded.delete(f"/categories/{created.json()['id']}").status_code == 204


def test_bulk_ok(seeded: TestClient) -> None:
    batch = [new_record("B-001"), new_record("B-002", category_id=2)]
    response = seeded.post("/records/bulk", json=batch)
    assert response.status_code == 201
    assert len(response.json()) == 2
    assert count(seeded) == 10


def test_bulk_rollback_duplicate(seeded: TestClient) -> None:
    batch = [new_record("B-001"), new_record("V06-01")]
    assert seeded.post("/records/bulk", json=batch).status_code == 409
    assert count(seeded) == 8
    codes = [r["code"] for r in seeded.get("/records").json()]
    assert "B-001" not in codes


def test_bulk_duplicate_inside_batch(seeded: TestClient) -> None:
    batch = [new_record("B-001"), new_record("B-001")]
    assert seeded.post("/records/bulk", json=batch).status_code == 409
    assert count(seeded) == 8


def test_bulk_missing_category(seeded: TestClient) -> None:
    batch = [new_record("B-001"), new_record("B-002", category_id=99)]
    assert seeded.post("/records/bulk", json=batch).status_code == 404
    assert count(seeded) == 8


def test_bulk_size_limits(seeded: TestClient) -> None:
    assert seeded.post("/records/bulk", json=[]).status_code == 422
    too_many = [new_record(f"B-{i:03d}") for i in range(101)]
    assert seeded.post("/records/bulk", json=too_many).status_code == 422


def test_sql_injection_is_data(seeded: TestClient) -> None:
    response = seeded.get("/records", params={"q": "' OR 1=1 --"})
    assert response.status_code == 200
    assert response.json() == []
    assert count(seeded) == 8


def test_persistence_between_connections(seeded: TestClient) -> None:
    seeded.post("/records", json=new_record())
    with sqlite3.connect(database.DATABASE_PATH) as connection:
        row = connection.execute(
            "SELECT COUNT(*) FROM records WHERE code = ?", ("V06-99",)
        ).fetchone()
    assert row[0] == 1
