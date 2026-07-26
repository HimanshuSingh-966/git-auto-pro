# Git-Auto Pro — development tasks.
#
# Common usage:
#   make install        # create venv and install the package (editable, with dev extras)
#   make test           # run the test suite
#   make clean          # remove build artifacts and caches
#   make help           # list all targets
#
# Override the Python interpreter / venv location if needed:
#   make install PYTHON=python3.11 VENV=.venv

PYTHON        ?= python3
VENV          ?= venv
VENV_BIN      := $(VENV)/bin
VENV_PYTHON  := $(VENV_BIN)/python
VENV_PIP     := $(VENV_BIN)/pip

# Source/test directories for linting/formatting/type-checking.
PKG := git_auto_pro tests

.PHONY: help install install-no-venv clean clean-venv clean-all \
        test test-cov lint format typecheck build publish-test publish \
        precommit check

help: ## Show this help message
	@echo "Git-Auto Pro — available targets:"
	@echo ""
	@awk 'BEGIN {FS = ":.*##"} \
		/^[a-zA-Z_-]+:.*##/ { printf "  \033[36m%-16s\033[0m %s\n", $$1, $$2 }' \
		$(MAKEFILE_LIST)
	@echo ""
	@echo "Override defaults: make install PYTHON=python3.11 VENV=.venv"

# ────────────────────────────── install ──────────────────────────────

install: $(VENV_BIN)/activate ## Create the virtualenv and install the package (editable, with dev extras)

$(VENV_BIN)/activate:
	@echo ">> Creating virtualenv at $(VENV)/"
	$(PYTHON) -m venv $(VENV)
	$(VENV_PYTHON) -m pip install --upgrade pip
	@echo ">> Installing git-auto-pro (editable, with dev extras)"
	$(VENV_PIP) install -e ".[dev]"
	@echo ""
	@echo "✅ Installed. Activate with: source $(VENV_BIN)/activate"
	@echo "   Then run: git-auto --help"

install-no-venv: ## Install (editable, with dev extras) into the current environment
	@echo ">> Installing git-auto-pro into the current environment"
	$(PYTHON) -m pip install --upgrade pip
	$(PYTHON) -m pip install -e ".[dev]"

# ────────────────────────────── clean ────────────────────────────────

CLEAN_PATHS := dist build *.egg-info htmlcov cover .coverage .coverage.* \
               .pytest_cache .mypy_cache .ruff_cache .tox .nox

clean: ## Remove build artifacts, coverage, and tool caches
	@echo ">> Removing build artifacts and caches"
	rm -rf $(CLEAN_PATHS)
	@find . -type d -name __pycache__ -not -path './$(VENV)/*' -exec rm -rf {} + 2>/dev/null || true

clean-venv: ## Remove the virtualenv
	@echo ">> Removing virtualenv at $(VENV)/"
	rm -rf $(VENV)

clean-all: clean clean-venv ## Remove everything: artifacts/caches and the virtualenv

# ────────────────────────────── quality ──────────────────────────────

test: ## Run the test suite
	@echo ">> Running tests"
	pytest

test-cov: ## Run the test suite with coverage (HTML + terminal)
	@echo ">> Running tests with coverage"
	pytest --cov=git_auto_pro --cov-report=html --cov-report=term
	@echo "Coverage report: htmlcov/index.html"

lint: ## Check formatting (black) and lint (ruff) without modifying files
	@echo ">> Linting"
	black --check $(PKG)
	ruff check $(PKG)

format: ## Format with black and auto-fix with ruff
	@echo ">> Formatting"
	black $(PKG)
	ruff check $(PKG) --fix

typecheck: ## Type-check with mypy
	@echo ">> Type checking"
	mypy git_auto_pro/

check: lint typecheck test ## Run lint + typecheck + tests (pre-PR gate)

# ────────────────────────────── build / publish ──────────────────────

build: clean ## Build sdist and wheel into dist/
	@echo ">> Building package"
	$(PYTHON) -m build
	@echo "Distribution files in dist/:"
	@ls -1 dist/

publish-test: build ## Build and upload to TestPyPI (verify before real release)
	@echo ">> Uploading to TestPyPI"
	$(PYTHON) -m twine upload --repository testpypi dist/*
	@echo "Verify with: pip install --index-url https://test.pypi.org/simple/ git-auto-pro"

publish: build ## Build and upload to PyPI
	@echo ">> Uploading to PyPI"
	$(PYTHON) -m twine upload dist/*

# ────────────────────────────── pre-commit ───────────────────────────

precommit: ## Install the pre-commit hooks locally
	@echo ">> Installing pre-commit hooks"
	pre-commit install
