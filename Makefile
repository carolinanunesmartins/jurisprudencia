# Commands are part of the contract in AGENTS.md §2: keep names stable.
.PHONY: setup verify lint test test-unit test-regression web-verify index fetch classify classify-replay detect export data-check web-dev

setup:
	uv sync
	npm --prefix web ci

verify: lint test web-verify

lint:
	uv run ruff check pipeline
	uv run ruff format --check pipeline

test: test-unit test-regression

test-unit:
	uv run pytest -m unit

test-regression:
	uv run pytest -m regression

web-verify:
	npm --prefix web run typecheck
	npm --prefix web run lint
	npm --prefix web run test
	npm --prefix web run build

# --- HUMAN-run only (crawl / live LLM). Not implemented yet: see ROADMAP M1, M2, M4, M5.
index:
	uv run python -m juris.crawl.index $(ARGS)
fetch:
	uv run python -m juris.crawl.fetch
classify:
	uv run python -m juris.classify --provider live
classify-replay:
	uv run python -m juris.classify --provider replay

# --- local, deterministic
detect:
	uv run python -m juris.detect
export:
	uv run python -m juris.export
data-check:
	uv run python -m juris.export.check

web-dev:
	npm --prefix web run dev
