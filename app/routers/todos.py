"""Todo router — /api/todos endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Response

from app.database import (
    create_todo,
    delete_todo,
    fetch_all_todos,
    fetch_todo_by_id,
    get_db,
    update_todo,
)
from app.models import TodoCreate, TodoResponse, TodoUpdate

router = APIRouter(prefix="/api/todos", tags=["todos"])


@router.get("/", response_model=list[TodoResponse])
async def list_todos(db=Depends(get_db)):
    """Return all todos ordered by position ASC, created_at DESC."""
    todos = await fetch_all_todos(db)
    return [TodoResponse(**{**t, "created_at": str(t["created_at"]), "completed_at": str(t["completed_at"]) if t["completed_at"] else None}) for t in todos]


@router.post("/", response_model=TodoResponse, status_code=201)
async def add_todo(body: TodoCreate, db=Depends(get_db)):
    """Create a new todo item."""
    todo = await create_todo(db, body.title)
    return TodoResponse(**{**todo, "created_at": str(todo["created_at"]), "completed_at": None})


@router.patch("/{todo_id}", response_model=TodoResponse)
async def update_todo_endpoint(todo_id: int, body: TodoUpdate, db=Depends(get_db)):
    """Update a todo's title and/or completed state."""
    if body.title is None and body.completed is None:
        raise HTTPException(status_code=400, detail="수정할 필드를 입력해주세요")

    existing = await fetch_todo_by_id(db, todo_id)
    if existing is None:
        raise HTTPException(status_code=404, detail="할 일을 찾을 수 없습니다")

    todo = await update_todo(db, todo_id, title=body.title, completed=body.completed)
    return TodoResponse(**{**todo, "created_at": str(todo["created_at"]), "completed_at": str(todo["completed_at"]) if todo["completed_at"] else None})


@router.delete("/{todo_id}", status_code=204)
async def delete_todo_endpoint(todo_id: int, db=Depends(get_db)):
    """Delete a todo item."""
    deleted = await delete_todo(db, todo_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="할 일을 찾을 수 없습니다")
    return Response(status_code=204)
