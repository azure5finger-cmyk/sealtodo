# 세션 — 2026-04-03 (1차)

TodoList MVP(v0.1.0) 구현 + 인프라 + 통합 검증.

## 타임라인

| 시각 | 요청 | 작업 | 결과 |
|---|---|---|---|
| 03:28 | `/init` + v5 문서 기반 진행 | CLAUDE.md를 v5 스펙으로 업데이트 | Testing/Security/Playwright 섹션 추가 |
| 03:30 | 인프라 파일 병렬 처리 | Makefile, STRATEGY.md, ci.yml 동시 생성 | 빈 상태 메시지 "오늘 할 일을 적어보세요"로 수정, opacity 0.35 |
| 03:36 | Playwright MCP 등록 | `claude mcp add playwright` | 세션에서 도구 로드 안 됨 → npm playwright로 전환 |
| 03:44 | Phase 4 통합 검증 | Playwright 스크립트로 9시나리오 자동 캡처 | 스크린샷 8개 생성 (docs/screenshots/final-*.png) |
| 03:46 | 커밋 + 태그 + 릴리즈 | `dd17ebc`, git tag v0.1.0 | GitHub Release 생성 완료 |
| 03:50 | 실행 확인 요청 | 서버 기동 (localhost:8001) | 콘솔에서 favicon 404 발견 |
| 03:51 | favicon 수정 | 인라인 SVG favicon 추가 | #2563EB 배경 + 체크마크 아이콘 |
| 03:53 | README 엄밀하게 리팩토링 | API 에러코드, Make 전체 명령어, 디자인 원칙 추가 | 77 insertions, 51 deletions |
| 03:55 | 전략/작업 엄밀성 검증 | 교차 검증 에이전트 실행 | 3가지 불일치 발견 |
| 03:58 | 불일치 수정 | f-string SQL 제거, 터치 타겟 44px, favicon | database.py 명시적 분기 쿼리로 교체 |
| 04:00 | GitHub Issues 엄밀성 검증 | `gh issue list` 확인 | Phase 1 미실행 발견 — 라벨/마일스톤/본문 없음 |
| 04:01 | GitHub Issues 정비 | 라벨 6개 + 마일스톤 + P0 본문 + P1 라벨 수정 | 5개 P0 closed, 마일스톤 closed |
| 04:02 | 수락 조건 전수 검증 | 이슈 #1-5의 30개 조건 vs 코드 대조 | 30/30 PASS |
| 04:03 | 커밋 + 푸시 | `a3ec36f` | 보안/접근성/UX 수정 반영 |
| 04:05 | AGENT_PROMPT.md 작성 | v5→v6 완전 재작성 | 하네스 8가지 방어, 교차 검증 체크리스트, 7건 오류 수정 |
| 04:06 | 파일명 리팩토링 | `todolist_claude_code_prompt_v5.md` → `AGENT_PROMPT.md` | v5 삭제, .gitignore 업데이트 |

## 발견된 문제 및 해결

### 교차 검증에서 발견 (3건)

| 문제 | 원인 | 해결 |
|---|---|---|
| `database.py`에 f-string SQL | CLAUDE.md "f-string SQL 금지" 정책 위반 | 명시적 if/elif 분기 쿼리로 교체 |
| 체크박스 20px, 삭제 버튼 32px | CLAUDE.md "터치 타겟 ≥ 44px" 미달 | `::after` pseudo-element로 히트 영역 확장 |
| favicon.ico 404 | 브라우저 기본 요청인데 파일 없음 | 인라인 SVG favicon (`<link rel="icon">`) |

### v5 문서 오류 (7건)

| 항목 | v5 값 | 실제 값 |
|---|---|---|
| CSS max-width | 640px | 560px |
| DB created_at | TEXT | TIMESTAMP |
| Phase 0 스키마 | position 없음 | position INTEGER NOT NULL DEFAULT 0 |
| 테스트 수 | 13개 | 14개 |
| TodoResponse | position 없음 | position 포함 |
| favicon | 미언급 | 인라인 SVG 필요 |
| update SQL | f-string 패턴 | 명시적 분기 |

### GitHub Issues 미정비 (Phase 1 미실행)

| 항목 | Before | After |
|---|---|---|
| P0 라벨 | 없음 | `P0:MVP`, `type:feature`, `status:done` |
| P1 라벨 | `P1`만 | `P1:Enhanced`, `type:feature` |
| 마일스톤 | 없음 | `v0.1.0-MVP` (closed, 5/5) |
| 이슈 본문 | 제목만 | 수락 조건 + 기술/UX/Playwright 명세 |
| P0 상태 | OPEN | CLOSED |

## 커밋 이력

```
a3ec36f  04:03  fix: 보안/접근성/UX 교차 검증 후 수정
dd17ebc  03:46  docs: Phase 4 통합 검증 — 인프라 파일 + Playwright 스크린샷 + v0.1.0 준비
0dee7d7  02:43  chore: 통합 테스트 통과 후 코드 정리
2b839e5  02:40  feat: 할 일 추가 및 목록 조회 기능 구현 (#1, #2)
404c27b  02:29  chore: 프로젝트 초기 구조 및 Harness 세팅
d11384b  01:20  feat: 할 일 추가 기능 구현
5ce5823  22:50  feat: Hello World 출력 기능 추가
4ded44f  22:34  프로젝트 초기 설정
```

## 핵심 교훈

1. **문서와 코드는 동시에 검증해야 한다** — CLAUDE.md에 "금지"라고 쓰고 코드에서 위반하면 에이전트가 혼란스러워진다.
2. **Phase 1(PM Agent)을 건너뛰면 안 된다** — 이슈 라벨/마일스톤/본문이 없으면 프로젝트 상태 추적이 불가능하다.
3. **LLM은 "안전하니까 괜찮다"고 판단한다** — f-string SQL이 화이트리스트 기반이라 안전해도, 문서화된 정책을 위반하면 일관성이 깨진다.
4. **시각적 크기 ≠ 터치 영역** — 20px 체크박스는 눈에 문제없지만 모바일에서 누르기 어렵다. `::after`로 보이지 않는 히트 영역을 확보한다.
5. **favicon은 빼먹기 쉽다** — 브라우저 콘솔을 확인하지 않으면 발견할 수 없다.

---

# 세션 — 2026-04-03 (2차)

문서 체계 정립 + AGENT_PROMPT.md 완성.

## 타임라인

| 시각 | 작업 | 결과 |
|---|---|---|
| 04:10 | AGENT_PROMPT.md v6 작성 | v5의 7건 오류 수정, 하네스 8가지 방어, 교차 검증 체크리스트 |
| 04:12 | 파일명 리팩토링 | todolist_claude_code_prompt_v5.md → AGENT_PROMPT.md |
| 04:15 | 문서 체계(§0) 추가 | 4개 문서 역할 분담, .gitignore 정책, 사용 시나리오 |
| 04:18 | AGENT_PROMPT.md를 docs/로 이동 | git 추적 대상으로 변경 |
| 04:20 | SESSION_LOG 운영 규칙(§0.5) 추가 | 갱신 시점, 형식, append only 규칙 |
| 04:21 | CLAUDE.md에 Session Log 섹션 추가 | 매 세션 자동 로드 → 커밋 전 갱신 리마인드 |
| 04:22 | README에 docs/ 구조 반영 | AGENT_PROMPT, STRATEGY, SESSION_LOG 명시 |

## 발견된 문제

| 문제 | 원인 | 해결 |
|---|---|---|
| AGENT_PROMPT.md가 gitignore됨 | 프롬프트 문서를 비밀로 취급 | 프로젝트 지식이므로 git 추적으로 변경 |
| SESSION_LOG가 1회성 | 갱신 규칙 없음 | §0.5에 append only 운영 규칙 정의 |

## 커밋

- (이 커밋) — docs: 문서 체계 정립 — AGENT_PROMPT, SESSION_LOG, 운영 규칙

## 교훈

1. **프롬프트 문서는 git에 포함해야 한다** — gitignore하면 clone 시 유실되어 프로젝트 재현이 불가능하다.
2. **문서 체계는 콘텍스트 윈도우를 고려해서 설계한다** — 항상 로드(CLAUDE.md)는 짧게, 상세(STRATEGY.md)는 참조로, 빌드 프롬프트(AGENT_PROMPT.md)는 수동 로드로 분리.
3. **누적 문서는 운영 규칙이 필요하다** — "언제, 어떤 형식으로, 누가 갱신하는가"를 명시하지 않으면 방치된다.
