.PHONY: setup dev test test-ci clean check find-port help

PORT ?= 8000

setup:  ## 의존성 설치
	uv sync

dev:  ## 개발 서버 (포트 자동 탐색: 8000→8001→8002)
	@AVAIL=$$(for p in $(PORT) $$(($(PORT)+1)) $$(($(PORT)+2)); do \
		netstat -ano 2>/dev/null | grep -q ":$$p " || { echo $$p; break; }; \
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
		netstat -ano 2>/dev/null | grep -q ":$$p " || { echo $$p; exit 0; }; \
	done; echo "No available port"

help:  ## 도움말
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-12s\033[0m %s\n", $$1, $$2}'

.DEFAULT_GOAL := help
