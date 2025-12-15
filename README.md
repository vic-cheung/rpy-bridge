# rpy-bridge

**rpy-bridge** is a Python-controlled **R execution orchestrator** that enables
Python code to run R functions, scripts, and packages with **reproducible
filesystem and environment semantics**.

It is built on top of `rpy2`, but unlike thin wrappers, rpy-bridge stabilizes how
R code is executed when invoked from Python: project roots are inferred, `renv`
environments can be activated out-of-tree, relative paths behave as expected,
and return values are normalized for safe Python consumption.

This makes rpy-bridge suitable for production pipelines, CI, and bilingual
Python/R teams where R code must run reliably outside an interactive R session.

**Latest release:** [`rpy-bridge` on PyPI](https://pypi.org/project/rpy-bridge/)

---

## What this is (and is not)

rpy-bridge **is not a thin rpy2 wrapper**.

Typical rpy2 usage assumes:
- the Python working directory is the R project root
- `renv` lives next to the executing script
- relative paths resolve correctly by default
- all R code executes in `globalenv()`

These assumptions break quickly in real-world Python workflows.

rpy-bridge instead provides a **controlled R runtime** with explicit guarantees
around execution context, filesystem behavior, and environment activation.

---

## Core capabilities

### 1. R execution orchestration

- Embeds R via `rpy2` with deterministic startup behavior
- Disables interactive and GUI-dependent hooks for headless execution
- Loads R scripts into isolated namespaces (not `globalenv()`)

### 2. Project root inference and path stability

- Infers R project roots using markers such as:
  `.git`, `.Rproj`, `renv.lock`, `DESCRIPTION`, `.here`
- Executes R code from the inferred project root regardless of Python CWD
- Preserves relative-path behavior expected by R scripts
- Supports R code using `here::here()` or project-local data

### 3. Out-of-tree `renv` activation

- Activates `renv` projects located **outside** the calling Python directory
- Sources `.Rprofile` and `.Renviron` to reproduce R startup semantics
- Does not require R scripts and `renv` to live in the same directory

### 4. Python ↔ R data conversion

- Converts Python scalars, lists, dicts, and pandas objects into R equivalents
- Converts R vectors, lists, and data.frames back into Python-native types
- Handles nested structures, missing values, and mixed types robustly

### 5. Data normalization and diagnostics

- Post-processes R data.frames to fix dtype, timezone, and NA semantics
- Normalizes column types for reliable Python-side comparison
- Supports structured mismatch diagnostics between Python and R data

### 6. Function invocation across scripts and packages

- Calls functions defined in sourced R scripts, base R, or installed packages
- Supports qualified function names (e.g. `stats::median`)
- Executes functions within the active project and library context

---

## Calling base R functions and managing packages

In addition to sourcing local R scripts, rpy-bridge supports calling functions
from base R and installed packages directly from Python.

Current support includes:

- Calling base R functions without a local R script
- Executing functions from installed R packages within the active environment

Planned extensions (roadmap):

- Programmatic installation of R packages into the active `renv` or system
  environment when explicitly enabled
- Declarative package requirements at the Python call site
- Safe, opt-in package installation for CI and ephemeral environments

Package installation is intentionally **not automatic by default** to preserve
reproducibility and avoid side effects during execution.

---

## Installation

### Prerequisites

- System R installed and available on `PATH`
- Python 3.12+

### From PyPI

Install rpy-bridge with rpy2 for full R support:

```bash
python3 -m pip install rpy-bridge rpy2
```

Using `uv`:

```bash
uv add rpy-bridge rpy2
```

### Development install

```bash
python3 -m pip install -e .
```

or:

```bash
uv sync
```

### Required Python dependencies

- `rpy2`
- `pandas`
- `numpy`

---

## Usage

### Call a function from a local R script

```python
from pathlib import Path
from rpy_bridge import RFunctionCaller

project_dir = Path("/path/to/your-r-project")
script = project_dir / "scripts" / "example.R"

caller = RFunctionCaller(
    path_to_renv=project_dir,
    script_path=script,
)

result = caller.call("some_function", 42, named_arg="value")
```

### Call base R functions (no local script)

```python
from rpy_bridge import RFunctionCaller

caller = RFunctionCaller(path_to_renv=None)

samples = caller.call("stats::rnorm", 10, mean=0, sd=1)
median_val = caller.call("stats::median", samples)
```

---

## Round-trip Python ↔ R behavior

rpy-bridge attempts to convert Python objects to R and back. Most objects used in
scientific and ML pipelines round-trip cleanly, but some heterogeneous Python
structures may be wrapped or slightly altered due to differences in R’s type
system.

| Python type                                    | Round-trip fidelity | Notes                                                                 |
| ---------------------------------------------- | ------------------- | --------------------------------------------------------------------- |
| `int`, `float`, `bool`, `str`                  | High                | Scalars convert directly                                              |
| Homogeneous `list` of numbers/strings          | High                | Converted to atomic R vectors                                         |
| Nested homogeneous lists                       | High                | Converted to nested R lists                                           |
| `pandas.DataFrame` / `pd.Series`               | High                | Converted to `data.frame` and normalized on return                    |
| Mixed-type `list` or `dict`                    | Partial             | May be wrapped in single-element vectors                              |
| `None` / `pd.NA`                               | High                | Converted to R `NULL`                                                 |

---

## R setup helpers

Helper scripts are provided in `examples/r-deps/` to prepare R environments.

- Install system R dependencies (macOS / Homebrew):

```bash
bash examples/r-deps/install_r_dev_deps_homebrew.sh
```

- Initialize an `renv` project:

```r
source("examples/r-deps/setup_env.R")
```

- Restore the environment on a new machine:

```r
renv::restore()
```

---

## Who this is for

rpy-bridge is designed for:

- Python-first pipelines that rely on mature R code
- Teams where R logic must remain authoritative
- CI or production systems that cannot rely on interactive R sessions
- Multi-repo or multi-directory projects with non-trivial filesystem layouts

It is **not** intended as a convenience wrapper for exploratory R usage.

---

## Licensing

- rpy-bridge is released under the MIT License © 2025 Victoria Cheung
- Depends on [`rpy2`](https://rpy2.github.io), licensed under the GNU GPL (v2 or later)

---

## Acknowledgements

This package was spun out of internal tooling I wrote at Revolution Medicines.
Thanks to the team there for supporting its open-source release.
