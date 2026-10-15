# Commands are part of the contract in AGENTS.md §2: keep names stable.
.PHONY: setup verify lint test test-unit test-regression web-verify index fetch classify classify-replay detect judge judge-replay export data-check snapshot snapshot-load evaluate web-dev

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

# --- HUMAN-run only: contacts dgsi.pt or the live LLM API (AGENTS.md rules 1 and 6)
index:
	uv run python -m juris.crawl.index $(ARGS)
fetch:
	uv run python -m juris.crawl.fetch $(ARGS)
classify:
	uv run python -m juris.classify --provider live $(ARGS)
classify-replay:
	uv run python -m juris.classify --provider replay $(ARGS)
judge:
	uv run python -m juris.detect.judge --provider live
judge-replay:
	uv run python -m juris.detect.judge --provider replay

# --- local, deterministic
detect:
	uv run python -m juris.detect
export:
	uv run python -m juris.export
data-check:
	uv run python -m juris.export.check
# committed results (data/classifications): dump after a run; load in a fresh clone
snapshot:
	uv run python -m juris.db.snapshot dump
snapshot-load:
	uv run python -m juris.db.snapshot load
# data/eval/report.md (needs the local database and data/replay/)
evaluate:
	uv run python -m juris.evaluate

web-dev:
	npm --prefix web run dev
