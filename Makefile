.PHONY: ensure-uv setup install-all ruff format lint test clean

# Detect uv binary (empty if not found)
UV_BIN := $(shell command -v uv 2>/dev/null)

ensure-uv:
ifndef UV_BIN
	@echo "[ERROR] 'uv' not found on PATH." >&2
	@echo "Install it (macOS/Linux) with:" >&2
	@echo "  curl -LsSf https://astral.sh/uv/install.sh | sh" >&2
	@exit 1
else
	@echo "[info] Using uv: $(UV_BIN)"
endif


# Create venv & install main + dev deps
setup: ensure-uv
	test -d .venv || uv venv .venv
	uv sync --all-extras
	uv run python -m ipykernel install --user --name=rpy-bridge --display-name "rpy-bridge"

# Install main dependencies + your package in editable mode
install-all:
	uv pip install -e ".[dev]"


ruff:
	uv run ruff check . --fix

format: ruff

ty:
	uv run ty check .

lint: ruff ty

test:
	uv run pytest -q

clean:
	rm -rf .venv
	rm -f uv.lock
