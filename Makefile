.PHONY: help install install-dev check type-check lint format test unused deps clean

help: ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install production dependencies
	pip install -r requirements.txt

install-dev: ## Install development dependencies
	pip install -r requirements.txt
	pip install -r requirements-dev.txt

type-check: ## Run type checking with mypy
	mypy --strict .

test: ## Run tests with pytest
	pytest

lint: ## Run linting with ruff
	ruff check .

format: ## Check formatting with black and isort
	black --check .
	isort --check-only .
	ruff format --check .

format-fix: ## Fix formatting with black, isort, and ruff
	ruff format .
	black .
	isort .

unused: ## Check for unused code and dependencies
	vulture . --min-confidence 80 --exclude venv --exclude tests
	deptry .

check: type-check test lint format unused ## Run all checks (full pipeline)

clean: ## Clean up generated files
	find . -type d -name "__pycache__" -exec rm -r {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -r {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -r {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -r {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -r {} + 2>/dev/null || true
	find . -type d -name "htmlcov" -exec rm -r {} + 2>/dev/null || true
	find . -type d -name ".coverage" -exec rm -r {} + 2>/dev/null || true
	rm -f .coverage coverage.xml

