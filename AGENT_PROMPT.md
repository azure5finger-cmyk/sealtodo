================================================================
TodoList 프로젝트 — Claude Code 자율 실행 프롬프트 (v6)
================================================================

실행 환경: macOS, uv, Python 3.12+, Claude Code (Max), Playwright
워크플로우: Issue → Branch → 구현 → pytest → Playwright 캡처 → PR → Merge
버전: v0.0.1 (Harness) → v0.1.0 (MVP)
최종 검증: 코드-문서-이슈 교차 검증 완료 (v5 대비 7개 오류 수정)

이 문서 하나로 Claude Code 에이전트가 처음부터 끝까지 자율 실행하여
미니멀 TodoList 웹 앱을 완성할 수 있다.


================================================================
0. 문서 체계 (Document Architecture)
================================================================

이 프로젝트는 4개의 문서가 역할을 분담한다.
각 문서의 위치, 로드 시점, 역할이 다르다.
이 구조를 Phase 0에서 반드시 생성해야 한다.

--------------------------------------------------
0.1 문서 역할 분담
--------------------------------------------------

```
docs/AGENT_PROMPT.md         ← 이 문서. 전체 빌드 프롬프트 (playbook)
CLAUDE.md                    ← 매 세션 자동 로드되는 규칙 (rulebook)
  @docs/STRATEGY.md          ← CLAUDE.md가 참조. 설계 원칙 + 하네스 방어
docs/SESSION_LOG.md          ← 세션별 작업 기록 (logbook)
```

■ docs/AGENT_PROMPT.md (이 문서)
  - 역할: 프로젝트를 처음부터 끝까지 빌드하는 자율 실행 프롬프트
  - 위치: docs/ (프로젝트 문서)
  - git 추적: O (프로젝트 지식이므로 반드시 git에 포함)
  - 자동 로드: X (너무 크므로 매 세션 로드하지 않음)
  - 사용법: "docs/AGENT_PROMPT.md를 읽고 Phase N부터 실행해"

■ CLAUDE.md
  - 역할: Claude Code가 매 세션 자동으로 읽는 규칙서
  - 위치: 프로젝트 루트 (Claude Code가 자동 인식하는 위치)
  - git 추적: O
  - 자동 로드: O (Claude Code가 세션 시작 시 자동 로드)
  - 내용: 짧고 핵심적 — Commands, Architecture, Code/UX/Testing/Security Rules
  - 크기 제한: 가능한 한 짧게. 상세 내용은 STRATEGY.md로 분리.

■ docs/STRATEGY.md
  - 역할: 설계 원칙 + LLM 하네스 방어 (CLAUDE.md의 확장)
  - 위치: docs/
  - git 추적: O
  - 자동 로드: O (CLAUDE.md의 @docs/STRATEGY.md 참조로 자동 로드)
  - 내용: 프로젝트 목적, 설계 원칙 4개, 하네스 방어 8개, 품질 기준

■ docs/SESSION_LOG.md
  - 역할: 세션별 작업 기록, 발견된 문제, 교훈 (누적 문서)
  - 위치: docs/
  - git 추적: O
  - 자동 로드: X
  - 갱신 시점: 매 세션에서 커밋 전에 해당 세션의 작업을 append
  - 사용법: 미래 세션에서 "docs/SESSION_LOG.md 읽어"로 이전 맥락 확인
  - 형식: 세션별 날짜 헤더(# 세션 — YYYY-MM-DD) 아래에 타임라인, 문제, 교훈 기록

--------------------------------------------------
0.2 왜 이 구조인가
--------------------------------------------------

■ 문제: LLM 에이전트는 콘텍스트 윈도우 크기에 제한이 있다.
  모든 정보를 CLAUDE.md에 넣으면:
  - 매 세션마다 불필요한 빌드 프롬프트가 로드됨
  - 콘텍스트 낭비 → 실제 작업에 쓸 공간 감소
  - 규칙이 길어지면 LLM이 후반부를 무시함

■ 해결: 계층적 분리
  ```
  항상 로드 (작음):  CLAUDE.md ──@──> docs/STRATEGY.md
  필요 시 로드 (큼): docs/AGENT_PROMPT.md
  사후 기록:          docs/SESSION_LOG.md
  ```

■ 설계 원칙:
  1. 자동 로드 문서는 짧게 — CLAUDE.md는 100줄 이내 목표
  2. 상세 내용은 참조로 분리 — @docs/STRATEGY.md
  3. 빌드 프롬프트는 수동 로드 — 초기 구축 시에만 필요
  4. 모든 문서는 git에 포함 — clone하면 즉시 사용 가능

--------------------------------------------------
0.3 .gitignore 정책
--------------------------------------------------

프로젝트 문서(AGENT_PROMPT.md, STRATEGY.md, SESSION_LOG.md)는
git에 반드시 포함한다. 제외 대상은 런타임 산출물뿐이다:

```
# 제외: 런타임 산출물
.env, .venv/, *.db, __pycache__/, .pytest_cache/
node_modules/, package.json, package-lock.json

# 제외: OS/IDE
.DS_Store, .idea/, .vscode/

# 포함: 프로젝트 문서 (절대 gitignore하지 않는다)
# docs/AGENT_PROMPT.md   ← git 추적
# docs/STRATEGY.md       ← git 추적
# docs/SESSION_LOG.md    ← git 추적
# CLAUDE.md              ← git 추적
```

--------------------------------------------------
0.4 사용 시나리오
--------------------------------------------------

■ 시나리오 A: 처음부터 프로젝트 빌드
  → "docs/AGENT_PROMPT.md를 읽고 Phase 0부터 실행해"

■ 시나리오 B: 특정 Phase만 실행
  → "docs/AGENT_PROMPT.md의 Phase 2를 읽고 Layer 1을 실행해"

■ 시나리오 C: 일반 개발 (기능 추가, 버그 수정)
  → CLAUDE.md + STRATEGY.md가 자동 로드됨. AGENT_PROMPT.md 불필요.

■ 시나리오 D: 이전 세션 맥락 확인
  → "docs/SESSION_LOG.md를 읽어"

■ 시나리오 E: 프로젝트를 다른 환경에서 재현
  → git clone → docs/AGENT_PROMPT.md를 읽고 Phase 0부터 실행
  → 모든 문서가 git에 포함되어 있으므로 추가 파일 불필요

--------------------------------------------------
0.5 SESSION_LOG.md 운영 규칙
--------------------------------------------------

SESSION_LOG.md는 누적 문서다. 세션마다 새 파일을 만들지 않고,
기존 파일에 새 세션 기록을 append한다.

■ 갱신 시점: 커밋 직전
  에이전트는 git commit을 실행하기 전에 해당 세션에서 수행한 작업을
  docs/SESSION_LOG.md에 추가해야 한다.

■ 갱신 형식:
  ```markdown
  ---

  # 세션 — YYYY-MM-DD (N차)

  ## 타임라인
  | 시각 | 작업 | 결과 |
  |---|---|---|
  | HH:MM | 무엇을 했는가 | 어떤 결과가 나왔는가 |

  ## 발견된 문제
  | 문제 | 원인 | 해결 |
  |---|---|---|

  ## 커밋
  - `hash` — 메시지

  ## 교훈
  - 이번 세션에서 배운 것 (미래 세션에 도움이 되는 것만)
  ```

■ 규칙:
  1. 새 세션은 `---` 구분선 + `# 세션 — 날짜` 헤더로 시작
  2. 같은 날 여러 세션이면 (1차), (2차)로 구분
  3. 이전 세션 내용은 수정하지 않는다 (append only)
  4. "교훈" 섹션에는 코드에서 직접 확인할 수 있는 것은 쓰지 않는다
     (예: "함수 X를 추가했다" ← 이건 git log로 보면 됨)
     미래 세션에서 같은 실수를 반복하지 않기 위한 판단 기준만 기록한다


================================================================
1. 엔지니어링 원칙
================================================================

이 프로젝트는 세 가지 엔지니어링 원칙 위에 설계되었다.
각 원칙은 LLM 에이전트의 체계적 실패 패턴을 방어한다.

--------------------------------------------------
1.1 프롬프트 엔지니어링 (Prompt Engineering)
--------------------------------------------------

LLM은 모호한 지시를 자기 방식대로 해석한다.
이 문서는 모호함을 제거하기 위해 아래 패턴을 따른다.

■ 규칙: 모든 지시는 검증 가능한 형태로 작성한다
  - BAD: "깔끔한 UI를 만들어"
  - GOOD: "색상 3가지만 사용: #FAFAFA, #1A1A1A, #2563EB. grep -c 'gradient' style.css → 0"

■ 규칙: 각 Phase는 완료 조건(Exit Criteria)으로 끝난다
  - 완료 조건을 만족하지 못하면 다음 Phase로 넘어가지 않는다
  - 완료 조건은 실행 가능한 명령어로 구성된다 (추측 금지)

■ 규칙: 코드 스펙은 정확한 값을 명시한다
  - BAD: "적당한 너비"
  - GOOD: "max-width: 560px"

■ 규칙: 에러 응답까지 명시한다
  - 성공 응답만 적으면 LLM은 에러 처리를 생략한다
  - 모든 엔드포인트에 성공 + 에러 응답 코드를 명시한다

--------------------------------------------------
1.2 콘텍스트 엔지니어링 (Context Engineering)
--------------------------------------------------

LLM은 콘텍스트가 길어지면 초기 지시를 잊고, 자기가 생성한 내용을 사실로 간주한다.

■ 규칙: 코드를 작성하기 전에 기존 코드를 먼저 읽는다
  - 새 함수를 호출하기 전: grep -n "def function_name" app/*.py
  - 새 CSS 클래스를 쓰기 전: grep "class_name" app/static/css/style.css
  - "아마 이럴 것이다"로 코드를 쓰지 않는다

■ 규칙: CLAUDE.md와 docs/STRATEGY.md를 매 Phase 시작 시 다시 읽는다
  - 콘텍스트가 길어지면 규칙을 잊는다
  - cat CLAUDE.md로 규칙을 리마인드한다

■ 규칙: 파일을 수정할 때 전체 파일을 읽은 뒤 수정한다
  - 부분만 읽고 수정하면 다른 부분과 충돌한다
  - 특히 style.css, app.js는 전체를 읽고 수정한다

■ 규칙: 숫자를 변경하면 모든 참조를 grep한다
  - grep -ri "이전값" . --include="*.md" --include="*.py" --include="*.js" --include="*.css"
  - CLAUDE.md, README.md, STRATEGY.md, 코드 모두 확인

--------------------------------------------------
1.3 하네스 엔지니어링 (Harness Engineering)
--------------------------------------------------

LLM은 강력하지만 체계적으로 실패하는 패턴이 있다.
아래 8가지 방어를 모든 Phase에서 적용한다.

① 할루시네이션 방어 (Hallucination)
   LLM은 존재하지 않는 함수, 파라미터를 자신 있게 사용한다.
   → 함수를 호출하기 전에 시그니처를 읽는다
   → 모르면 먼저 읽는다. 가정하지 않는다.

② 확증 편향 방어 (Confirmation Bias)
   같은 접근이 실패해도 "이번엔 되겠지"라고 반복한다.
   → 같은 접근 2번 실패 시 접근 자체를 바꾼다. 3번째 시도 금지.
   → 실패 시 "왜 실패했는가"를 먼저 진단한다.

③ 유령 수정 방어 (Phantom Fix)
   "수정했습니다"라고 하지만 실제로는 해결되지 않았다.
   → 수정 후 반드시 make test 실행
   → "논리적으로 맞을 것"을 신뢰하지 않는다

④ 스코프 팽창 방어 (Scope Creep)
   요청 이상을 "개선"하려 한다.
   → Issue에 정의된 수락 조건만 구현한다
   → "이것도 같이 하면 좋겠다"는 하지 않는다

⑤ 숫자 전파 방어 (Stale Number Propagation)
   한 곳의 숫자를 바꾸고 다른 참조를 업데이트하지 않는다.
   → 숫자 변경 시 grep -ri "이전값"으로 전수 검색

⑥ 테스트 환각 방어 (Test Illusion)
   테스트가 통과하지만 실제로는 타겟 코드를 실행하지 않는다.
   → pytest-asyncio fixture는 반드시 @pytest_asyncio.fixture 사용
   → 조건부 로직 안에 핵심 assertion을 넣지 않는다

⑦ 보안 정책 위반 방어 (Security Policy Violation)
   "안전하니까 괜찮다"고 판단하고 문서화된 규칙을 위반한다.
   → CLAUDE.md에 "f-string SQL 금지"라면 코드에서도 금지
   → 화이트리스트라도 f-string으로 SQL을 생성하지 않는다
   → 정책을 바꾸고 싶으면 CLAUDE.md를 수정한다. 코드에 예외를 넣지 않는다.

⑧ 접근성 누락 방어 (Accessibility Omission)
   시각적으로 문제없어 보여도 터치/클릭 영역이 부족하다.
   → 인터랙티브 요소의 터치 타겟 ≥ 44px (WCAG)
   → 시각적 크기가 작으면 ::after pseudo-element로 히트 영역 확장


================================================================
2. 사전 준비 (1회)
================================================================

아래를 Claude Code에 입력:

---

아래 도구를 확인하고 설치해.

## 1. 사전 확인
```bash
gh auth status
uv --version
which npx
```

## 2. Playwright 설치 (스크린샷 캡처용)
```bash
npm install --no-save playwright
npx playwright install chromium
```

모든 명령이 성공하면 "준비 완료"라고 알려줘.
실패하는 항목이 있으면 해결 방법을 제시하고 재시도해.

---


================================================================
3. Phase 0 — Harness 세팅
================================================================

아래를 Claude Code에 입력:

---

cd ~/Documents/my-todo-app

이 프로젝트의 Harness를 세팅해. 기능은 구현하지 마. 빈 껍데기만.

## 프로젝트 개요
미니멀 TodoList 웹 앱. "AI가 만든 것 같지 않은" UX가 핵심.
MUJI 스타일 — 꾸미지 않아서 아름다운 것.

## 패키지 관리: uv (pip/requirements.txt 사용 금지)
```bash
uv init --bare
uv add fastapi "uvicorn[standard]" aiosqlite jinja2
uv add --dev pytest "pytest-asyncio>=0.23" httpx
```

pyproject.toml에 반드시 추가:
```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
```

## 생성할 파일 목록

### 1. Makefile
```makefile
.PHONY: setup dev test clean check find-port help

PORT ?= 8000

setup:  ## 의존성 설치
	uv sync

dev:  ## 개발 서버 (포트 자동 탐색: 8000→8001→8002)
	@AVAIL=$$(for p in $(PORT) $$(($(PORT)+1)) $$(($(PORT)+2)); do \
		lsof -ti:$$p >/dev/null 2>&1 || { echo $$p; break; }; \
	done); \
	echo "→ http://localhost:$$AVAIL"; \
	uv run uvicorn app.main:app --reload --port $$AVAIL

test:  ## pytest 실행
	uv run pytest tests/ -v

test-ci:  ## CI 환경 테스트
	uv run pytest tests/ -v --tb=short

clean:  ## DB 및 캐시 정리
	rm -f *.db
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true

check:  ## 서버 헬스체크 (포트 자동 탐색)
	@for p in 8000 8001 8002; do \
		curl -sf http://localhost:$$p/api/todos/ >/dev/null 2>&1 \
		&& { echo "OK on port $$p"; exit 0; }; \
	done; echo "Server not running"

find-port:  ## 사용 가능한 포트 출력
	@for p in 8000 8001 8002 8003; do \
		lsof -ti:$$p >/dev/null 2>&1 || { echo $$p; exit 0; }; \
	done; echo "No available port"

help:  ## 도움말
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-12s\033[0m %s\n", $$1, $$2}'

.DEFAULT_GOAL := help
```

### 2. .github/workflows/ci.yml
```yaml
name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Install uv
        uses: astral-sh/setup-uv@v4

      - name: Install dependencies
        run: uv sync

      - name: Run tests
        run: make test-ci

      - name: API smoke test
        run: |
          uv run uvicorn app.main:app --port 8000 &
          sleep 3
          curl -sf http://localhost:8000/api/todos/ | python3 -m json.tool
          kill %1
```

### 3. CLAUDE.md
```markdown
# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

@docs/STRATEGY.md

## Project
미니멀 TodoList 웹 앱. UX 최우선. MUJI 스타일의 절제된 디자인.
Python 3.12, uv, SQLite (aiosqlite), FastAPI, Vanilla JS, Bootstrap 5 CDN.
Linter: 없음 (소규모 프로젝트). CI: GitHub Actions (test + smoke).

## Commands
make setup       # uv sync
make dev         # 서버 (포트 자동 탐색: 8000→8001→8002)
make test        # pytest
make clean       # DB/캐시 정리
make check       # 헬스체크
make find-port   # 사용 가능한 포트 출력
단독 테스트: uv run pytest tests/test_todos.py::test_name

## Architecture
app/main.py → app/routers/todos.py → app/database.py
                                    → app/models.py
의존성 방향: models → database → routers → main (역방향 참조 금지)

DB as sole integration point:
- app/database.py만 aiosqlite를 import
- 다른 모듈은 database.py의 함수를 통해서만 DB 접근
- get_db()는 async generator → Depends(get_db)로 주입
- row_factory = aiosqlite.Row 설정됨
- 테스트는 tmp_path로 독립 DB 격리

DB schema: Single todos table — id (autoincrement PK), title, completed (bool),
position (int, for ordering), created_at (timestamp).
New todos get position = MAX(position) + 1.

Frontend: app.js가 /api/todos/와 fetch로 통신. SPA 방식 — 페이지 새로고침 금지.
Optimistic UI updates with rollback on error.

## Code Rules
- RESTful API: /api/todos, /api/todos/{id}
- Pydantic 모델로 모든 요청/응답 타입 정의
- 에러: 400 (잘못된 입력), 404 (존재하지 않는 리소스), 422 (검증 실패)
- docstring: 모든 함수, 클래스에 필수
- 커밋 메시지: feat:/fix:/docs:/test:/chore: + 한국어 설명
- innerHTML 금지 (체크마크 등 정적 요소 제외) → textContent 사용

## UX Rules
- 색상: #FAFAFA(배경), #1A1A1A(텍스트), #2563EB(강조)
- 추가 허용: #E5E5E5(border), #DC2626(에러), #fff
- border-radius ≤ 8px
- box-shadow: 0 1px 3px rgba(0,0,0,0.08) — 1단계만
- 이모지/gradient/외부 아이콘 라이브러리 금지 (HTML entity만: ✓는 &#10003;)
- 체크박스: div + CSS 커스텀 (네이티브 checkbox 금지)
- 빈 상태: 반드시 디자인 (opacity 0.35, 중앙 정렬)
- 로딩/에러 피드백: 반드시 구현
- transition/animation: CSS only (JS 애니메이션 금지)
- 여백: 아이템 padding ≥ 12px, 터치 타겟 ≥ 44px
- Bootstrap 기본 스타일을 커스텀 CSS로 덮어써서 "Bootstrap스러움" 제거

## Testing Rules
- pyproject.toml에 asyncio_mode = "auto" 설정됨
- 비동기 fixture: @pytest_asyncio.fixture (not @pytest.fixture)
- 테스트 함수에 @pytest.mark.asyncio 붙이지 않음 (auto 모드)
- 각 테스트: tmp_path로 독립 DB 사용
- 테스트 클라이언트: httpx.AsyncClient + ASGITransport

## Security Rules
- SQL Injection: 파라미터 바인딩 ? 사용 (f-string SQL 금지)
- XSS: textContent 사용 (innerHTML 금지, 정적 요소 제외)
- 입력 검증: Pydantic 모델에서 서버 측 검증

## Playwright 검증
- 구현 후 반드시 Playwright로 브라우저 캡처
- 스크린샷: docs/screenshots/에 저장
- PR 본문에 스크린샷 첨부
- 포트 자동 탐색: make find-port로 확인 후 접속
```

### 4. docs/STRATEGY.md
(전략 정의서 — LLM 하네스 8가지 방어를 포함. 이 문서의 §1.3 내용을 마크다운으로 작성.)

### 5. .gitignore
```
# Environment
.env
.venv/
venv/

# Python
__pycache__/
*.pyc
*.pyo
.pytest_cache/

# Database
*.db
*.sqlite3

# Node (Playwright capture script dependencies)
node_modules/
package.json
package-lock.json

# IDE
.idea/
.vscode/
*.swp

# OS
.DS_Store
Thumbs.db
```

### 6. 빈 껍데기 앱 파일

**app/main.py**: FastAPI 앱 생성, Jinja2 템플릿 마운트, static 마운트, 라우터 include, lifespan에서 init_db 호출, GET / → index.html 렌더링

**app/database.py**:
- DATABASE_PATH = "todo.db"
- init_db(): todos 테이블 생성
  ```sql
  CREATE TABLE IF NOT EXISTS todos (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      title TEXT NOT NULL,
      completed BOOLEAN NOT NULL DEFAULT 0,
      position INTEGER NOT NULL DEFAULT 0,
      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
  )
  ```
- get_db(): async generator (aiosqlite, row_factory = aiosqlite.Row)

**app/models.py**: 빈 파일 (Phase 2에서 Pydantic 모델 추가)

**app/routers/todos.py**: APIRouter(prefix="/api/todos", tags=["todos"]) — 엔드포인트 없이 빈 라우터

**app/templates/index.html**:
- Bootstrap 5 CDN link
- 인라인 SVG favicon (강조색 #2563EB 배경 + 체크마크)
- "Todo App" h1 제목
- form#todo-form: input#todo-input (placeholder="할 일을 입력하세요") + button.todo-submit "추가"
- div#todo-list-container: ul#todo-list + p#empty-state "오늘 할 일을 적어보세요" + p#error-state hidden
- /static/css/style.css 링크, /static/js/app.js script

**app/static/css/style.css**:
- CSS 변수: --color-bg: #FAFAFA, --color-text: #1A1A1A, --color-accent: #2563EB, --color-border: #E5E5E5, --shadow: 0 1px 3px rgba(0,0,0,0.08), --radius: 6px, --transition: 0.2s ease
- body: system-font stack, -webkit-font-smoothing: antialiased
- .container: max-width: 560px, margin: 0 auto
- .empty-state: text-align: center, opacity: 0.35

**app/static/js/app.js**: 주석 한 줄 — "// Todo App - Frontend Logic"

**tests/test_todos.py**: docstring 한 줄 — '"""API tests for todo operations."""'

## Phase 0 완료 조건
```bash
make dev &
sleep 3
make check        # → "OK on port XXXX"
kill %1
make test         # → 0 tests (수집만 확인)
git add . && git commit -m "chore: Harness 세팅 — uv, Makefile, CI, CLAUDE.md, STRATEGY.md"
git tag v0.0.1 && git push origin main --tags
```

---


================================================================
4. Phase 1 — PM Agent (GitHub Issues)
================================================================

아래를 Claude Code에 입력:

---

PM 역할로 GitHub Issues를 세팅해.

## 1단계: 라벨 생성
```bash
gh label create "P0:MVP" --color "B60205" --description "MVP 필수" --force
gh label create "P1:Enhanced" --color "0E8A16" --description "MVP 이후" --force
gh label create "type:feature" --color "1D76DB" --description "새 기능" --force
gh label create "status:ready" --color "FBCA04" --description "구현 가능" --force
gh label create "status:in-progress" --color "D93F0B" --description "구현 중" --force
gh label create "status:done" --color "0E8A16" --description "완료" --force
```

## 2단계: 마일스톤 생성
```bash
gh api repos/{owner}/{repo}/milestones \
  -f title="v0.1.0-MVP" \
  -f description="핵심 CRUD + 미니멀 UX 완성"
```

## 3단계: P0 이슈 5개 생성

모든 P0 이슈에 반드시: 라벨 `P0:MVP`, `type:feature`, `status:ready` + 마일스톤 `v0.1.0-MVP`

각 이슈 본문 형식:
```markdown
## 설명
[사용자 관점에서 이 기능이 왜 필요한지]

## 수락 조건 (Acceptance Criteria)
- [ ] 조건 1 (구체적, 테스트 가능)
- [ ] 조건 2

## 기술 명세
- 엔드포인트: [HTTP 메서드] [경로]
- 요청: { "field": "type" }
- 성공 응답: [상태 코드] + 형식
- 에러 응답: [상태 코드] + 조건

## UX 명세
- 사용자 흐름, 상태 처리, 애니메이션

## Playwright 검증 항목
- [ ] 캡처 1: [무엇을 검증]

## 의존 관계
- Depends on: #N 또는 없음
```

### Issue #1: feat: 할 일 추가
수락 조건:
- [ ] 텍스트 입력 후 Enter 키로 추가됨
- [ ] "추가" 버튼 클릭으로도 추가됨
- [ ] 빈 입력 시 shake 애니메이션 + border 빨간색
- [ ] 공백만 있는 입력도 거부 (서버 Pydantic 검증)
- [ ] 추가 후 입력 필드 자동 비움 + focus 유지
- [ ] 추가 후 목록에 즉시 반영 (새로고침 없음)
- [ ] 제목 앞뒤 공백 자동 제거

기술 명세:
- POST /api/todos/ → 201 + TodoResponse
- 요청: { "title": "string" }
- 에러: 422 (빈 제목/공백만)

Depends on: 없음

### Issue #2: feat: 할 일 목록 조회
수락 조건:
- [ ] 페이지 로드 시 전체 목록 자동 조회
- [ ] 할 일 없을 때: "오늘 할 일을 적어보세요" (opacity 0.35)
- [ ] 서버 에러 시: "목록을 불러오지 못했습니다"
- [ ] 로딩 중: 목록 영역 opacity 0.4
- [ ] 항목 있으면 빈 상태 숨김

기술 명세:
- GET /api/todos/ → 200 + list[TodoResponse]
- 정렬: position ASC, created_at DESC

Depends on: 없음

### Issue #3: feat: 완료/미완료 토글
수락 조건:
- [ ] 커스텀 원형 체크박스 클릭 시 전환
- [ ] 완료: 체크마크 + 취소선 + opacity 0.5
- [ ] 미완료 되돌리기 가능
- [ ] Optimistic Update + 서버 실패 시 롤백
- [ ] 새로고침 후에도 상태 유지

기술 명세:
- PATCH /api/todos/{id} → 200 + TodoResponse
- 요청: { "completed": true/false }
- 에러: 404

Depends on: #2

### Issue #4: feat: 할 일 삭제
수락 조건:
- [ ] × 버튼은 hover 시에만 opacity 전환으로 노출
- [ ] 클릭 시 확인 없이 즉시 삭제
- [ ] fade-out 0.3s 애니메이션 (opacity 0 → max-height 0)
- [ ] 애니메이션 완료 후 DOM에서 제거
- [ ] 마지막 항목 삭제 시 빈 상태 다시 표시
- [ ] 서버 실패 시 롤백

기술 명세:
- DELETE /api/todos/{id} → 204
- 에러: 404

Depends on: #2

### Issue #5: feat: 인라인 수정
수락 조건:
- [ ] 더블클릭 → span→input 교체
- [ ] 기존 텍스트 + auto focus + select
- [ ] Enter: 저장 (빈 입력이면 원래 텍스트 유지)
- [ ] Esc: 취소
- [ ] blur: 저장
- [ ] 완료된 항목은 편집 불가
- [ ] 서버 실패 시 원래 텍스트 복귀

기술 명세:
- PATCH /api/todos/{id} → 200 + TodoResponse
- 요청: { "title": "string" }
- 에러: 400 (필드 없음), 404, 422 (빈 제목)

Depends on: #2

## 4단계: P1 이슈 2개
라벨: `P1:Enhanced`, `type:feature` (마일스톤 없음)

#6: feat: 드래그 앤 드롭 순서 변경
#7: feat: 완료된 항목 일괄 삭제

## 5단계: 확인
```bash
gh issue list --state open --json number,title,labels,milestone
```
P0 이슈 5개에 라벨 3개 + 마일스톤 확인.

---


================================================================
5. Phase 2~3 — 구현 (Layer 1 + Layer 2)
================================================================

의존 관계에 따라 2개 Layer로 나눈다.
```
Layer 1 (독립): Issue #1 + #2 → 하나의 PR
Layer 2 (#2 의존): Issue #3 + #4 + #5 → 하나의 PR
```

--------------------------------------------------
5.1 Layer 1 프롬프트
--------------------------------------------------

아래를 Claude Code에 입력:

---

Issue #1, #2를 처리해. 아래 워크플로우를 자율 실행해.

## Step 1. Branch 생성
```bash
git checkout main && git pull origin main
git checkout -b feature/issue-1-2-crud-base
gh issue edit 1 --remove-label "status:ready" --add-label "status:in-progress"
gh issue edit 2 --remove-label "status:ready" --add-label "status:in-progress"
```

## Step 2. 이슈 확인
```bash
gh issue view 1
gh issue view 2
```
수락 조건을 하나하나 읽어.

## Step 3. 구현

### [콘텍스트 엔지니어링] 구현 전 반드시 실행:
```bash
cat CLAUDE.md                           # 규칙 리마인드
grep -n "def " app/database.py          # 기존 함수 확인
```

### 3-1. app/models.py
- TodoCreate: title (str) + @field_validator로 strip + 빈 문자열 거부
- TodoUpdate: title (Optional[str]), completed (Optional[bool]) + validator
- TodoResponse: id (int), title (str), completed (bool), position (int), created_at (str)
- 에러 메시지는 한국어: "할 일 내용을 입력해주세요"

### 3-2. app/database.py — CRUD 함수 추가
- fetch_all_todos(db) → list[dict]: ORDER BY position ASC, created_at DESC
- create_todo(db, title) → dict: position = COALESCE(MAX(position), -1) + 1
- fetch_todo_by_id(db, todo_id) → dict | None
- update_todo(db, todo_id, title=None, completed=None) → dict | None
  ⚠️ [하네스 §⑦]: f-string SQL 금지. 명시적 분기로 쿼리 작성:
  ```python
  if title is not None and completed is not None:
      await db.execute("UPDATE todos SET title = ?, completed = ? WHERE id = ?", ...)
  elif title is not None:
      await db.execute("UPDATE todos SET title = ? WHERE id = ?", ...)
  elif completed is not None:
      await db.execute("UPDATE todos SET completed = ? WHERE id = ?", ...)
  ```
- delete_todo(db, todo_id) → bool

### 3-3. app/routers/todos.py
- GET /api/todos/ → 200 + list[TodoResponse]
- POST /api/todos/ → 201 + TodoResponse
- PATCH /api/todos/{id} → 200 + TodoResponse
  - 400 if title=None and completed=None
  - 404 if not found
- DELETE /api/todos/{id} → 204
  - 404 if not found

### 3-4. app/templates/index.html
- Bootstrap 5 CDN
- 인라인 SVG favicon: `<link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'><rect width='32' height='32' rx='6' fill='%232563EB'/><path d='M9 17l4 4 10-10' stroke='white' stroke-width='3' fill='none' stroke-linecap='round' stroke-linejoin='round'/></svg>">`
- form#todo-form, input#todo-input, button.todo-submit
- div#todo-list-container, ul#todo-list, p#empty-state, p#error-state

### 3-5. app/static/css/style.css
CLAUDE.md UX Rules를 엄격히 따라:
- CSS 변수: --color-bg, --color-text, --color-accent, --color-border, --shadow, --radius: 6px, --transition: 0.2s ease
- .container: max-width: 560px
- .todo-form, .todo-input (focus 시 border-color: accent), .todo-submit
- .todo-list, .todo-item (fadeIn), .todo-item.completed .todo-title (취소선 + opacity 0.5)
- .todo-item.removing (opacity 0 + max-height 0, transition 0.3s)
- .todo-checkbox (커스텀 원형 20px) + ::after로 터치 타겟 44px 확보
- .todo-checkbox-mark (체크마크, display: none → block)
- .todo-title, .todo-edit-input (border: 1px solid accent)
- .todo-delete (opacity 0) + hover (0.3) + ::after로 터치 타겟 44px
- .todo-input.shake (@keyframes shake + border-color: #DC2626)
- .empty-state (opacity: 0.35, 중앙), .error-state (#DC2626)
- .loading (opacity 0.4)

### 3-6. app/static/js/app.js
- API_URL = "/api/todos"
- DOM 요소: todoForm, todoInput, todoList, emptyState, errorState, listContainer
- fetchTodos(): GET → renderTodos() + loading/error 처리
- addTodo(title): POST → todos.push + render
- toggleTodo(id, completed): PATCH + Optimistic Update + 실패 시 롤백
- deleteTodo(id): DELETE
- updateTodoTitle(id, title): PATCH
- renderTodos(): DOM 생성 + 빈 상태 토글
- createTodoElement(todo): li (checkbox + title + delete)
- handleToggle(todo): classList.toggle + toggleTodo + 롤백
- handleDelete(li, id): maxHeight 설정 → .removing → transitionend → remove()
- startEditing(li, todo): 더블클릭 → input 교체 + Enter/Esc/blur + saved 플래그
- todoForm submit: preventDefault, trim, shake if empty, addTodo
- **textContent 사용** (innerHTML은 체크마크 정적 요소만)
- fetchTodos() 호출 (초기화)

### 3-7. tests/test_todos.py
14개 테스트:
```
1.  test_list_todos_empty          → 200 + []
2.  test_list_todos_with_items     → 200 + 개수 확인
3.  test_create_todo_success       → 201 + 반환값
4.  test_create_todo_empty_title   → 422
5.  test_create_todo_whitespace    → 422
6.  test_create_todo_strips_ws     → 201 + trimmed
7.  test_toggle_todo_complete      → 200 + completed=true
8.  test_toggle_todo_incomplete    → 200 + completed=false
9.  test_update_todo_title         → 200 + 새 제목
10. test_update_todo_empty_title   → 422
11. test_update_todo_not_found     → 404
12. test_update_todo_no_fields     → 400
13. test_delete_todo_success       → 204 + 목록 0
14. test_delete_todo_not_found     → 404
```

테스트 패턴 (CLAUDE.md Testing Rules 준수):
```python
@pytest_asyncio.fixture(autouse=True)
async def setup_db(tmp_path):
    test_db_path = str(tmp_path / "test.db")
    db_module.DATABASE_PATH = test_db_path
    await init_db()
    yield
    if os.path.exists(test_db_path):
        os.remove(test_db_path)

@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
```

## Step 4. 테스트
```bash
make test
```
[하네스 §③]: FAIL이면 에러 메시지를 읽고 수정. "논리적으로 맞을 것"을 신뢰하지 마.
[하네스 §②]: 같은 접근 2번 실패 시 접근 자체를 바꿔.

## Step 5. Playwright 검증
```bash
PORT=$(make find-port)
uv run uvicorn app.main:app --port $PORT &
SERVER_PID=$!
sleep 3
```

Playwright 스크립트(scripts/capture-screenshots.mjs)를 작성하여 캡처:
1. 빈 상태 → docs/screenshots/issue-1-2-empty.png
2. "우유 사기" 추가 → docs/screenshots/issue-1-2-added.png
3. 빈 입력 시도 → docs/screenshots/issue-1-2-shake.png
4. 3개 항목 → docs/screenshots/issue-1-2-list.png

```bash
kill $SERVER_PID
make clean
```

## Step 6. Evaluation (실행 기반 — 추측 금지)

### 6-1. 기능 정합성
```bash
make test    # → 14/14 PASS
```

### 6-2. 코드 품질
```bash
grep -c "def " app/database.py       # ≥ 7
grep -c '"""' app/routers/todos.py    # ≥ 5
```

### 6-3. UX 품질
```bash
grep -c "gradient" app/static/css/style.css       # → 0
grep -c "location.reload" app/static/js/app.js    # → 0
```

### 6-4. 보안
```bash
grep -c 'f"' app/database.py                      # → 0 (f-string SQL 없음)
grep -n "innerHTML" app/static/js/app.js           # 정적 체크마크 외 없음
grep -c "field_validator" app/models.py            # ≥ 2
```

### 6-5. 접근성
```bash
grep -c "::after" app/static/css/style.css         # ≥ 2 (터치 타겟)
```

**하나라도 FAIL → Step 3으로. 전체 PASS → Step 7로.**

## Step 7. 커밋 + PR
```bash
git add .
git commit -m "feat: 할 일 추가 및 목록 조회 기능 구현 (#1, #2)"
git push origin feature/issue-1-2-crud-base
```

```bash
gh pr create \
  --title "feat: 할 일 추가 + 목록 조회 + CRUD API (#1, #2)" \
  --body "## 변경 사항
- POST /api/todos/ (201): 할 일 추가, 빈 입력 거부 (422)
- GET /api/todos/ (200): 전체 목록 조회
- PATCH /api/todos/{id} (200): 제목 수정, 완료 토글
- DELETE /api/todos/{id} (204): 삭제
- 빈 상태/로딩/에러 상태 처리
- UX: MUJI 스타일, 색상 3가지, 이모지 없음

## 스크린샷
| 빈 상태 | 추가 후 | shake | 목록 |
|---|---|---|---|
| ![](docs/screenshots/issue-1-2-empty.png) | ![](docs/screenshots/issue-1-2-added.png) | ![](docs/screenshots/issue-1-2-shake.png) | ![](docs/screenshots/issue-1-2-list.png) |

## 테스트
pytest: 14/14 PASS

Closes #1
Closes #2" \
  --base main
```

## Step 8. Merge + 정리
```bash
PR_NUM=$(gh pr list --head feature/issue-1-2-crud-base --json number -q '.[0].number')
gh pr merge $PR_NUM --squash --delete-branch
gh issue edit 1 --remove-label "status:in-progress" --add-label "status:done"
gh issue edit 2 --remove-label "status:in-progress" --add-label "status:done"
git checkout main && git pull origin main
```

---

--------------------------------------------------
5.2 Layer 2 프롬프트
--------------------------------------------------

아래를 Claude Code에 입력:

---

Layer 1이 merge되었어. Issue #3, #4, #5를 처리해.

## Step 1. Branch
```bash
git checkout main && git pull origin main
git checkout -b feature/issue-3-4-5-interactions
gh issue edit 3 --remove-label "status:ready" --add-label "status:in-progress"
gh issue edit 4 --remove-label "status:ready" --add-label "status:in-progress"
gh issue edit 5 --remove-label "status:ready" --add-label "status:in-progress"
```

## Step 2. 이슈 확인 + 기존 코드 확인
```bash
gh issue view 3 && gh issue view 4 && gh issue view 5
cat CLAUDE.md
grep -n "def " app/database.py
grep -n "function " app/static/js/app.js
```
[콘텍스트 엔지니어링]: 기존 코드를 먼저 읽어야 한다.

## Step 3. 구현
Layer 1에서 만든 코드 위에 추가. 기존 동작을 깨뜨리지 마.
[하네스 §④]: 요청된 #3, #4, #5만 구현. 추가 개선은 하지 마.

추가 구현:
- #3: handleToggle() — Optimistic Update + classList.toggle + 서버 실패 시 롤백
- #4: handleDelete() — maxHeight → reflow → .removing → transitionend → remove()
- #4: .todo-delete CSS — opacity 0, hover 시 0.3
- #5: startEditing() — if (todo.completed) return → span→input → Enter/Esc/blur
- #5: saved 플래그로 중복 저장 방지

## Step 4~8: Layer 1과 동일한 패턴
(테스트 → Playwright → Evaluation → 커밋 → PR → Merge)

---


================================================================
6. Phase 4 — 통합 검증 + v0.1.0 릴리즈
================================================================

아래를 Claude Code에 입력:

---

모든 P0 이슈가 merge되었어. 통합 검증 후 v0.1.0을 릴리즈해.

## Step 1. 통합 Playwright 검증

### 서버 실행
```bash
make clean
PORT=$(make find-port)
uv run uvicorn app.main:app --port $PORT &
SERVER_PID=$!
sleep 3
```

### 9개 시나리오 (Playwright 스크립트로 자동화)
scripts/capture-screenshots.mjs를 작성하여 실행:

1. 첫 방문 — 빈 상태 → final-01-empty.png
2. "우유 사기" 추가 → final-02-first-todo.png
3. "빨래 돌리기", "이메일 확인", "운동하기" 추가 → final-03-multiple.png
4. "우유 사기" 완료 토글 → final-04-completed.png
5. 완료 되돌리기 (스크린샷 생략)
6. "빨래 돌리기" → "빨래 돌리고 널기" 편집 → final-05-edited.png
7. "운동하기" 삭제 → final-06-deleted.png
8. 빈 입력 거부 → final-07-shake.png
9. 새로고침 후 데이터 유지 → final-08-after-refresh.png

```bash
npm install --no-save playwright 2>/dev/null
PORT=$PORT node scripts/capture-screenshots.mjs
kill $SERVER_PID
```

## Step 2. 테스트
```bash
make test    # → 14/14 PASS
```

## Step 3. README.md 최종 업데이트
스크린샷 테이블, 주요 기능, API 문서 (요청/응답/에러), Make 명령어 전체, 디자인 원칙, 프로젝트 구조, 버전 히스토리 포함.

## Step 4. 커밋 + 태그 + 릴리즈
```bash
make clean
git add .
git commit -m "docs: Phase 4 통합 검증 — 스크린샷 + README 업데이트"
git tag v0.1.0
git push origin main --tags
```

```bash
gh release create v0.1.0 \
  --title "v0.1.0 — MVP" \
  --notes "## 주요 기능
- 할 일 추가 (Enter/버튼, 빈 입력 shake)
- 목록 조회 (빈 상태/로딩/에러)
- 완료/미완료 토글 (Optimistic Update)
- 삭제 (hover 노출, fade-out)
- 인라인 편집 (더블클릭, Enter/Esc)

## 실행 방법
make setup && make dev"
```

## Step 5. 마일스톤 닫기
```bash
MILESTONE_NUM=$(gh api repos/{owner}/{repo}/milestones --jq '.[0].number')
gh api repos/{owner}/{repo}/milestones/$MILESTONE_NUM -X PATCH -f state="closed"
```

## Step 6. 최종 확인
```bash
gh issue list --state open --label "P0:MVP"    # → 결과 없어야 함
gh release view v0.1.0                          # → 릴리즈 존재
echo "=== v0.1.0 릴리즈 완료 ==="
```

---


================================================================
7. 교차 검증 체크리스트
================================================================

마지막으로 아래를 Claude Code에 입력하여 전체 일관성을 검증한다:

---

프로젝트 전체를 교차 검증해. 아래 항목을 실행해서 확인해.

## 문서-코드 일관성
```bash
# CLAUDE.md의 색상 규칙 vs 실제 CSS
grep -c "#FAFAFA\|#1A1A1A\|#2563EB" app/static/css/style.css  # ≥ 3
grep -c "gradient" app/static/css/style.css                     # → 0

# CLAUDE.md의 보안 규칙 vs 실제 코드
grep -c 'f"' app/database.py                                    # → 0
grep -n "innerHTML" app/static/js/app.js                        # 정적만

# CLAUDE.md의 터치 타겟 규칙 vs 실제 CSS
grep -c "::after" app/static/css/style.css                      # ≥ 2

# README의 테스트 수 vs 실제
grep -c "^async def test_" tests/test_todos.py                  # → 14
```

## 이슈-코드 일관성
```bash
# 모든 P0 이슈가 닫혔는가
gh issue list --state open --label "P0:MVP"     # → 결과 없음

# 마일스톤이 닫혔는가
gh api repos/{owner}/{repo}/milestones?state=closed --jq '.[].title'  # → v0.1.0-MVP

# 릴리즈가 존재하는가
gh release view v0.1.0 --json tagName -q '.tagName'  # → v0.1.0
```

## favicon 확인
```bash
grep -c 'rel="icon"' app/templates/index.html   # → 1
```

하나라도 FAIL이면 수정하고 다시 확인해.

---


================================================================
8. 주의사항 (실행 중 발견된 문제 + 해결)
================================================================

| # | 문제 | 원인 | 해결 |
|---|---|---|---|
| 1 | pytest-asyncio 전체 FAIL | asyncio_mode 미설정 | pyproject.toml에 asyncio_mode = "auto" |
| 2 | 포트 8000 충돌 | 다른 서비스 사용 중 | make find-port로 자동 탐색 |
| 3 | innerHTML XSS | 사용자 입력을 innerHTML에 삽입 | textContent 사용 (정적만 허용) |
| 4 | f-string SQL 정책 위반 | "안전하니까" 판단하고 위반 | 명시적 분기 쿼리 (하네스 §⑦) |
| 5 | 터치 타겟 < 44px | 시각적으로 문제없어 보임 | ::after pseudo-element (하네스 §⑧) |
| 6 | favicon 404 | 기본 요청인데 누락 | 인라인 SVG favicon |
| 7 | 같은 에러 3번 반복 | LLM 확증 편향 | 2번 실패 시 접근 변경 (하네스 §②) |
| 8 | "수정했다"고 하지만 FAIL | 유령 수정 | make test 필수 실행 (하네스 §③) |
| 9 | 이슈 라벨/마일스톤 누락 | Phase 1 미실행 | PM Agent Phase 완전 실행 |
| 10 | DB 스키마에 position 누락 | 문서에 미기재 | Phase 0부터 position 포함 |
| 11 | created_at TEXT vs TIMESTAMP | 문서 오류 | TIMESTAMP DEFAULT CURRENT_TIMESTAMP |
| 12 | max-width 640 vs 560 | 문서 오류 | 560px이 정확한 값 |
| 13 | 테스트 13개 vs 14개 | test_update_no_fields 누락 | 400 에러 테스트 포함하여 14개 |


================================================================
9. 전체 플로우 요약
================================================================

```
사전 준비     gh 인증 + uv + Playwright 설치

Phase 0      Harness 세팅
             ├── uv init → pyproject.toml
             ├── Makefile (포트 자동 탐색)
             ├── .github/workflows/ci.yml
             ├── CLAUDE.md (@docs/STRATEGY.md)
             ├── docs/STRATEGY.md (하네스 8가지 방어)
             ├── 빈 껍데기 앱 (favicon 포함)
             └── git tag v0.0.1

Phase 1      PM Agent
             ├── 라벨 6개, 마일스톤 1개
             ├── P0 이슈 5개 (수락 조건 + 기술/UX/Playwright 명세)
             └── P1 이슈 2개

Phase 2~3    Layer 1: #1 + #2
             ├── 구현 (콘텍스트 엔지니어링 적용)
             ├── make test → 14/14 PASS
             ├── Playwright 캡처 4개
             ├── Evaluation 5개 카테고리
             ├── PR → Merge
             └── Issue → status:done

             Layer 2: #3 + #4 + #5
             ├── 기존 코드 위에 추가
             ├── make test → 전체 PASS
             ├── Playwright 캡처 6개
             ├── PR → Merge
             └── Issue → status:done

Phase 4      통합 검증 + 릴리즈
             ├── Playwright 9시나리오 (스크린샷 8개)
             ├── README (스크린샷 + API 문서 + 디자인 원칙)
             ├── git tag v0.1.0
             ├── gh release create
             ├── 마일스톤 close
             └── 교차 검증 (문서-코드-이슈 일관성)
```
