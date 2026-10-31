.PHONY: setup data-check audit train stress consistency figures readme test web-dev web-build all
setup:
	uv sync --locked
	cd web && npm ci
data-check:
	uv run lidcheck data-check
audit:
	uv run lidcheck audit
train:
	uv run lidcheck train
stress:
	uv run lidcheck stress
	uv run lidcheck transfer
consistency:
	uv run lidcheck consistency
figures:
	uv run lidcheck figures
readme:
	uv run lidcheck readme
	uv run python scripts/check_readme_results.py
test:
	uv run ruff check
	uv run ruff format --check
	uv run pytest
	cd web && npm run lint && npm test && npm run build && npm run test:e2e
	uv run python scripts/check_readme_results.py --check
web-dev:
	cd web && npm run dev
web-build:
	cd web && npm run build
all: setup audit train stress consistency figures readme test
