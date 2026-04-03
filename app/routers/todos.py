"""Todo router — /api/todos endpoints."""

from fastapi import APIRouter

router = APIRouter(prefix="/api/todos", tags=["todos"])


@router.get("/")
async def list_todos_stub():
    """Stub endpoint — returns empty list (Phase 0 harness)."""
    return []
