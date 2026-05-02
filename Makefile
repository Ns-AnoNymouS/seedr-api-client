SRC = src/ tests/

.PHONY: help fmt lint typecheck test cov check ci fix

help:
	@echo "Usage: make <target>"
	@echo ""
	@echo "  fmt        Auto-format code with ruff"
	@echo "  lint       Run ruff linter"
	@echo "  typecheck  Run mypy --strict"
	@echo "  test       Run pytest (no coverage)"
	@echo "  cov        Run pytest with coverage report"
	@echo "  check      Run lint + typecheck + tests"
	@echo "  ci         Exact replica of the GitHub Actions CI job"
	@echo "  fix        Auto-fix lint issues and format"

fmt:
	ruff format $(SRC)

lint:
	ruff check $(SRC)

typecheck:
	mypy src/seedr_api/ --strict

test:
	pytest tests/ -v

cov:
	pytest tests/ -v --cov=seedr_api --cov-report=term-missing

check: lint typecheck test

ci: lint typecheck
	pytest tests/ -v --cov=seedr_api --cov-report=xml

fix:
	ruff check --fix $(SRC)
	ruff format $(SRC)
