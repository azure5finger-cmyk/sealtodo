"""API tests for todo operations."""

import os

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

import app.database as db_module
from app.database import init_db
from app.main import app


@pytest_asyncio.fixture(autouse=True)
async def setup_db(tmp_path):
    """Isolate each test with its own DB."""
    test_db_path = str(tmp_path / "test.db")
    db_module.DATABASE_PATH = test_db_path
    await init_db()
    yield
    if os.path.exists(test_db_path):
        os.remove(test_db_path)


@pytest_asyncio.fixture
async def client():
    """Async HTTP client pointed at the ASGI app."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


async def test_list_todos_empty(client):
    """GET /api/todos/ returns 200 with empty list when no todos exist."""
    res = await client.get("/api/todos/")
    assert res.status_code == 200
    assert res.json() == []


async def test_list_todos_with_items(client):
    """GET /api/todos/ returns all created todos."""
    await client.post("/api/todos/", json={"title": "첫 번째"})
    await client.post("/api/todos/", json={"title": "두 번째"})
    res = await client.get("/api/todos/")
    assert res.status_code == 200
    assert len(res.json()) == 2


async def test_create_todo_success(client):
    """POST /api/todos/ returns 201 with the created todo."""
    res = await client.post("/api/todos/", json={"title": "우유 사기"})
    assert res.status_code == 201
    data = res.json()
    assert data["title"] == "우유 사기"
    assert data["completed"] is False
    assert "id" in data


async def test_create_todo_empty_title(client):
    """POST /api/todos/ with empty title returns 422."""
    res = await client.post("/api/todos/", json={"title": ""})
    assert res.status_code == 422


async def test_create_todo_whitespace(client):
    """POST /api/todos/ with whitespace-only title returns 422."""
    res = await client.post("/api/todos/", json={"title": "   "})
    assert res.status_code == 422


async def test_create_todo_strips_ws(client):
    """POST /api/todos/ trims leading/trailing whitespace from title."""
    res = await client.post("/api/todos/", json={"title": "  청소하기  "})
    assert res.status_code == 201
    assert res.json()["title"] == "청소하기"


async def test_toggle_todo_complete(client):
    """PATCH /api/todos/{id} sets completed=true."""
    create = await client.post("/api/todos/", json={"title": "운동"})
    todo_id = create.json()["id"]
    res = await client.patch(f"/api/todos/{todo_id}", json={"completed": True})
    assert res.status_code == 200
    assert res.json()["completed"] is True


async def test_toggle_todo_incomplete(client):
    """PATCH /api/todos/{id} can toggle back to completed=false."""
    create = await client.post("/api/todos/", json={"title": "운동"})
    todo_id = create.json()["id"]
    await client.patch(f"/api/todos/{todo_id}", json={"completed": True})
    res = await client.patch(f"/api/todos/{todo_id}", json={"completed": False})
    assert res.status_code == 200
    assert res.json()["completed"] is False


async def test_update_todo_title(client):
    """PATCH /api/todos/{id} updates the title."""
    create = await client.post("/api/todos/", json={"title": "구매"})
    todo_id = create.json()["id"]
    res = await client.patch(f"/api/todos/{todo_id}", json={"title": "장보기"})
    assert res.status_code == 200
    assert res.json()["title"] == "장보기"


async def test_update_todo_empty_title(client):
    """PATCH /api/todos/{id} with empty title returns 422."""
    create = await client.post("/api/todos/", json={"title": "구매"})
    todo_id = create.json()["id"]
    res = await client.patch(f"/api/todos/{todo_id}", json={"title": ""})
    assert res.status_code == 422


async def test_update_todo_not_found(client):
    """PATCH /api/todos/{id} with non-existent id returns 404."""
    res = await client.patch("/api/todos/9999", json={"completed": True})
    assert res.status_code == 404


async def test_update_todo_no_fields(client):
    """PATCH /api/todos/{id} with no fields returns 400."""
    create = await client.post("/api/todos/", json={"title": "구매"})
    todo_id = create.json()["id"]
    res = await client.patch(f"/api/todos/{todo_id}", json={})
    assert res.status_code == 400


async def test_delete_todo_success(client):
    """DELETE /api/todos/{id} returns 204 and removes the todo."""
    create = await client.post("/api/todos/", json={"title": "삭제 테스트"})
    todo_id = create.json()["id"]
    res = await client.delete(f"/api/todos/{todo_id}")
    assert res.status_code == 204
    list_res = await client.get("/api/todos/")
    assert list_res.json() == []


async def test_delete_todo_not_found(client):
    """DELETE /api/todos/{id} with non-existent id returns 404."""
    res = await client.delete("/api/todos/9999")
    assert res.status_code == 404
