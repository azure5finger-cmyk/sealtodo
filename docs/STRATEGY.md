# STRATEGY.md — 설계 원칙 + LLM 하네스 방어

## 프로젝트 목적

"AI가 만든 것 같지 않은" 미니멀 TodoList 웹 앱.
MUJI 스타일 — 꾸미지 않아서 아름다운 것.
사용자가 할 일을 빠르게 입력하고, 완료 체크하고, 삭제하는 흐름이 핵심.

## 설계 원칙 4가지

### 1. DB as sole integration point
- `app/database.py`만 `aiosqlite`를 import
- 다른 모듈은 `database.py`의 함수를 통해서만 DB 접근
- `get_db()`는 async generator → `Depends(get_db)`로 주입
- `row_factory = aiosqlite.Row` 항상 설정

### 2. SPA (Single Page Application)
- `app.js`가 `/api/todos/*`와 `fetch`로 통신
- 페이지 새로고침 금지 (`location.reload` 금지)
- Optimistic UI Update + 서버 실패 시 롤백

### 3. MUJI UX
- 색상 5가지 이내: #FAFAFA, #1A1A1A, #2563EB, #E5E5E5, #DC2626
- border-radius ≤ 8px
- box-shadow 1단계만
- 이모지/gradient/외부 아이콘 라이브러리 금지

### 4. 보안 우선
- f-string SQL 금지 → 파라미터 바인딩 `?` 사용
- innerHTML 금지 → textContent 사용 (정적 요소 제외)
- 입력 검증: Pydantic 서버 측 검증

## LLM 하네스 방어 8가지

### ① 할루시네이션 방어
함수를 호출하기 전에 시그니처를 읽는다.
모르면 먼저 읽는다. 가정하지 않는다.

### ② 확증 편향 방어
같은 접근 2번 실패 시 접근 자체를 바꾼다. 3번째 시도 금지.
실패 시 "왜 실패했는가"를 먼저 진단한다.

### ③ 유령 수정 방어
수정 후 반드시 `make test` 실행.
"논리적으로 맞을 것"을 신뢰하지 않는다.

### ④ 스코프 팽창 방어
Issue에 정의된 수락 조건만 구현한다.
"이것도 같이 하면 좋겠다"는 하지 않는다.

### ⑤ 숫자 전파 방어
숫자 변경 시 `grep -ri "이전값"`으로 전수 검색.

### ⑥ 테스트 환각 방어
pytest-asyncio fixture는 반드시 `@pytest_asyncio.fixture` 사용.
조건부 로직 안에 핵심 assertion을 넣지 않는다.

### ⑦ 보안 정책 위반 방어
CLAUDE.md에 "f-string SQL 금지"라면 코드에서도 금지.
정책을 바꾸고 싶으면 CLAUDE.md를 수정한다. 코드에 예외를 넣지 않는다.

### ⑧ 접근성 누락 방어
인터랙티브 요소의 터치 타겟 ≥ 44px (WCAG).
시각적 크기가 작으면 `::after` pseudo-element로 히트 영역 확장.

## 품질 기준

| 항목 | 기준 |
|---|---|
| 테스트 | 14/14 PASS |
| gradient | grep → 0 |
| location.reload | grep → 0 |
| f-string SQL | grep → 0 |
| ::after 터치타겟 | grep ≥ 2 |
| field_validator | grep ≥ 2 |
