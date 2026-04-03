"""Database module — aiosqlite wrapper with CRUD operations."""

from typing import Optional

import aiosqlite

DATABASE_PATH = "todo.db"


async def init_db() -> None:
    """Initialize the database and create tables if not exist."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS todos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                completed BOOLEAN NOT NULL DEFAULT 0,
                position INTEGER NOT NULL DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP DEFAULT NULL
            )
        """)
        # 기존 DB 마이그레이션: completed_at 컬럼이 없으면 추가
        try:
            await db.execute("ALTER TABLE todos ADD COLUMN completed_at TIMESTAMP DEFAULT NULL")
        except Exception:
            pass  # 이미 존재하면 무시
        await db.commit()


async def get_db():
    """Async generator that yields a database connection."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        yield db


async def fetch_all_todos(db: aiosqlite.Connection) -> list[dict]:
    """Fetch all todos ordered by position ASC, created_at DESC."""
    cursor = await db.execute(
        "SELECT id, title, completed, position, created_at, completed_at FROM todos ORDER BY position ASC, created_at DESC"
    )
    rows = await cursor.fetchall()
    return [dict(row) for row in rows]


async def create_todo(db: aiosqlite.Connection, title: str) -> dict:
    """Create a new todo with position = MAX(position) + 1."""
    cursor = await db.execute(
        "SELECT COALESCE(MAX(position), -1) + 1 FROM todos"
    )
    row = await cursor.fetchone()
    position = row[0]

    cursor = await db.execute(
        "INSERT INTO todos (title, completed, position) VALUES (?, 0, ?)",
        (title, position),
    )
    await db.commit()
    todo_id = cursor.lastrowid
    return await fetch_todo_by_id(db, todo_id)


async def fetch_todo_by_id(db: aiosqlite.Connection, todo_id: int) -> Optional[dict]:
    """Fetch a single todo by ID. Returns None if not found."""
    cursor = await db.execute(
        "SELECT id, title, completed, position, created_at, completed_at FROM todos WHERE id = ?",
        (todo_id,),
    )
    row = await cursor.fetchone()
    return dict(row) if row else None


async def update_todo(
    db: aiosqlite.Connection,
    todo_id: int,
    title: Optional[str] = None,
    completed: Optional[bool] = None,
) -> Optional[dict]:
    """Update a todo's title and/or completed state. Returns None if not found."""
    if title is not None and completed is not None:
        if completed:
            await db.execute(
                "UPDATE todos SET title = ?, completed = ?, completed_at = CURRENT_TIMESTAMP WHERE id = ?",
                (title, completed, todo_id),
            )
        else:
            await db.execute(
                "UPDATE todos SET title = ?, completed = ?, completed_at = NULL WHERE id = ?",
                (title, completed, todo_id),
            )
    elif title is not None:
        await db.execute(
            "UPDATE todos SET title = ? WHERE id = ?",
            (title, todo_id),
        )
    elif completed is not None:
        if completed:
            await db.execute(
                "UPDATE todos SET completed = ?, completed_at = CURRENT_TIMESTAMP WHERE id = ?",
                (completed, todo_id),
            )
        else:
            await db.execute(
                "UPDATE todos SET completed = ?, completed_at = NULL WHERE id = ?",
                (completed, todo_id),
            )
    await db.commit()
    return await fetch_todo_by_id(db, todo_id)


async def delete_todo(db: aiosqlite.Connection, todo_id: int) -> bool:
    """Delete a todo by ID. Returns True if deleted, False if not found."""
    cursor = await db.execute(
        "DELETE FROM todos WHERE id = ?", (todo_id,)
    )
    await db.commit()
    return cursor.rowcount > 0
