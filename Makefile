.PHONY: ensure-uv setup install-all ruff format lint ty test clean

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

# --------------------------------------
# Linting with timestamped output
# --------------------------------------
RUFF_DIR:= $(CURDIR)/.ruff_checks
RUFF_TIMESTAMP := $(shell date +%Y%m%d_%H%M%S)
RUFF_OUTPUT := $(RUFF_DIR)/ruff_$(RUFF_TIMESTAMP).txt
UNAME_S := $(shell uname -s)

ruff:
	@mkdir -p $(RUFF_DIR)
	@echo "Running ruff..."
	@RUFF_OUTPUT=$(RUFF_DIR)/ruff_$(shell date +%Y%m%d_%H%M%S).txt; \
	uv run ruff check . --fix > $$RUFF_OUTPUT 2>&1; \
	RU_RC=$$?; \
	if [ $$RU_RC -ne 0 ]; then \
		echo "[ruff reported issues or failed (exit code $$RU_RC)] See details: $$RUFF_OUTPUT"; \
		case "$$(uname -s)" in \
			Darwin) open $$RUFF_OUTPUT ;; \
			Linux) xdg-open $$RUFF_OUTPUT ;; \
			Windows_NT) start $$RUFF_OUTPUT ;; \
			*) echo "Cannot auto-open file on this OS. File saved as: $$RUFF_OUTPUT" ;; \
		esac; \
		exit $$RU_RC; \
	else \
		echo "✅ Ruff check passed! No issues."; \
		rm -f $$RUFF_OUTPUT; \
	fi


format: ruff

# --------------------------------------
# Type checking with timestamped output
# --------------------------------------
TY_DIR := $(CURDIR)/.ty_checks
TY_TIMESTAMP := $(shell date +%Y%m%d_%H%M%S)
TY_OUTPUT := $(TY_DIR)/ty_$(TY_TIMESTAMP).txt
UNAME_S := $(shell uname -s)

ty:
	@mkdir -p $(TY_DIR)
	@echo "Running ty..."
	@TY_OUTPUT=$(TY_DIR)/ty_$(shell date +%Y%m%d_%H%M%S).txt; \
	uv run ty check . > $$TY_OUTPUT 2>&1; \
	if grep -q "error\[" $$TY_OUTPUT; then \
		echo "[Type errors found] See details: $$TY_OUTPUT"; \
		case "$$(uname -s)" in \
			Darwin) open $$TY_OUTPUT ;; \
			Linux) xdg-open $$TY_OUTPUT ;; \
			Windows_NT) start $$TY_OUTPUT ;; \
			*) echo "Cannot auto-open file on this OS. File saved as: $$TY_OUTPUT" ;; \
		esac; \
	else \
		echo "✅ Type check passed! No errors."; \
		rm -f $$TY_OUTPUT; \
	fi


lint: ruff ty

test:
	uv run pytest -q

clean:
	rm -rf .venv
	rm -f uv.lock
