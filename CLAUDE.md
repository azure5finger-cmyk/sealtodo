# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Minimal TodoList web app. UX-first. MUJI style — beauty through restraint, not decoration.

- **Backend:** Python 3.12+, FastAPI, aiosqlite (SQLite), Jinja2
- **Frontend:** Vanilla HTML/CSS/JS, Bootstrap 5 CDN (overridden to remove Bootstrap look)
- **Package manager:** `uv` (never pip or requirements.txt)
- **CI:** GitHub Actions (test + smoke)

To build from scratch, read `docs/AGENT_PROMPT.md` and execute from Phase 0.

## Commands

```bash
make setup       # uv sync (install dependencies)
make dev         # start dev server (auto port-find: 8000→8001→8002)
make test        # run pytest
make test-ci     # CI variant with --tb=short
make clean       # remove *.db and __pycache__
make check       # health check against running server
make find-port   # print first available port

# Run a single test
uv run pytest tests/test_todos.py::test_name
```

## Architecture

```
app/main.py → app/routers/todos.py → app/database.py
                                    → app/models.py
```

Dependency direction: `models` → `database` → `routers` → `main` (no back-references).

**DB as sole integration point:**
- Only `app/database.py` imports `aiosqlite`
- Other modules access the DB only through `database.py` functions
- `get_db()` is an async generator injected via `Depends(get_db)`
- `row_factory = aiosqlite.Row` is always set

**DB schema** — single `todos` table:
```sql
id INTEGER PRIMARY KEY AUTOINCREMENT,
title TEXT NOT NULL,
completed BOOLEAN NOT NULL DEFAULT 0,
position INTEGER NOT NULL DEFAULT 0,  -- new todos: MAX(position)+1
created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
```

**Frontend:** `app.js` communicates with `/api/todos/*` via `fetch`. Full SPA — no page refreshes. Optimistic UI updates with rollback on error.

## Code Rules

- RESTful API at `/api/todos` and `/api/todos/{id}`
- All request/response types defined with Pydantic models
- Error codes: 400 (bad input), 404 (not found), 422 (validation failure)
- Commit messages: `feat:/fix:/docs:/test:/chore:` + Korean description
- `innerHTML` is forbidden except for static elements (e.g., checkmarks) — use `textContent`
- **f-string SQL is forbidden** — always use parameterized queries with `?`

## UX Rules

- Colors: `#FAFAFA` (bg), `#1A1A1A` (text), `#2563EB` (accent), `#E5E5E5` (border), `#DC2626` (error), `#fff`
- `border-radius` ≤ 8px; `box-shadow` max one level: `0 1px 3px rgba(0,0,0,0.08)`
- No emoji, no gradients, no external icon libraries — use HTML entities (checkmark: `&#10003;`)
- Custom CSS checkboxes only — no native `<input type="checkbox">`
- Empty state must be designed: centered, `opacity: 0.35`, text "오늘 할 일을 적어보세요"
- Loading and error feedback are required
- Transitions/animations: CSS only — no JS animations
- Item padding ≥ 12px; touch targets ≥ 44px (use `::after` pseudo-element to extend hit area if visual size is smaller)
- Container: `max-width: 560px`, centered

## Testing Rules

- `pyproject.toml` must have `asyncio_mode = "auto"` under `[tool.pytest.ini_options]`
- Async fixtures: use `@pytest_asyncio.fixture` (not `@pytest.fixture`)
- Do not add `@pytest.mark.asyncio` to test functions (auto mode handles it)
- Each test uses an isolated DB via `tmp_path`
- Test client: `httpx.AsyncClient` with `ASGITransport`

## Playwright Validation

After implementing features, capture browser screenshots with Playwright:
- Save to `docs/screenshots/`
- Attach screenshots to PR descriptions
- Use `make find-port` to determine the running server port
