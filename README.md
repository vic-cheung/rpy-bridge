# rpy-bridge

rpy-bridge is a Python-to-R a robust interoperability engine that combines environment management, type-safe conversions, data normalization, and safe function execution to make Python-R collaboration seamless.

It enables Python developers to call R functions, scripts, and packages safely while preserving type fidelity and project-specific R environments. This is ideal for bilingual teams where R authors maintain core logic, and Python-centric users need reliable access without rewriting code.

**Latest release:** [`rpy-bridge` on PyPI](https://pypi.org/project/rpy-bridge/)

---

## Key layers and capabilities

### 1. Lazy and robust R integration

- Automatically detects or sets R_HOME and ensures rpy2 is installed.
- Configures platform-specific dynamic library paths for macOS/Linux.

### 2. Environment management

- Activates renv projects and loads project-specific libraries if it exists, otherwise use current environemnt.
- Sources .Renviron and .Rprofile files to replicate the R project environment in Python.

### 3. Python ↔ R type conversion

- Converts Python scalars, lists, dicts, and pandas DataFrames into appropriate R objects.
- Converts R atomic vectors, ListVector/NamedList, and data.frames back into Python-native objects.
- Handles nested structures, mixed types, and missing values robustly (NA_* → None/pd.NA).

### 4. Data hygiene and normalization

- Post-processes R DataFrames: fixes dtypes, numeric/date conversions, and timezone issues.
- Normalizes and aligns column types for accurate Python comparisons.
- Supports comparing Python and R DataFrames with mismatch diagnostics.

### 5. Function calling

- Calls functions from R scripts, base R, or installed packages safely.
- Automatically converts arguments and return values, including keyword arguments.
- Supports mixed data types, nested structures, and DataFrames seamlessly.

### 6. Python-first workflow for R code

- Enables Python developers to reuse R functions without needing deep R knowledge.
- Keeps network, token, and SSL concerns outside the package when sourcing scripts locally.
- Designed for reproducibility and safe execution in CI or cross-platform environments.

---

## Installation

**Prerequisites**

- System R installed and available on `PATH` (rpy2 requires a working R installation).
- Python 3.12+

**From PyPI:**

```bash
python3 -m pip install rpy-bridge
```

or using `uv`:

```bash
uv add rpy-bridge
```

**During development (editable install):**

```bash
python3 -m pip install -e .
```

or using `uv`:

```bash
uv sync
```

**Required Python packages** (the installer will pull these in):

- `rpy2` (GPLv2 or later)
- `pandas`
- `numpy`

---

## Usage

```python
from pathlib import Path
from rpy_bridge import RFunctionCaller

rfc = RFunctionCaller(
    path_to_renv=Path("/path/to/project"),
    script=Path("/path/to/script.R"),
)

summary_df = rfc.call("summarize_cohort", cohort_df)
```

---

## Round-trip Python ↔ R behavior

`rpy-bridge` attempts to convert Python objects to R and back. Most objects used in scientific/ML pipelines round-trip cleanly, but some heterogeneous Python structures may be wrapped or slightly altered. This is normal due to R's type system.

| Python type                                    | Round-trip fidelity | Notes                                                                 |
| ---------------------------------------------- | ------------------- | --------------------------------------------------------------------- |
| `int`, `float`, `bool`, `str`                  | ✅ High              | Scalars convert directly                                              |
| Homogeneous `list` of numbers/strings/booleans | ✅ High              | Converted to atomic R vectors                                         |
| Nested lists of homogeneous types              | ✅ High              | Converted to nested R `ListVector`                                    |
| `pandas.DataFrame` / `pd.Series`               | ✅ High              | Converted to `data.frame` / R vector, post-processed back             |
| Mixed-type `list` or heterogeneous `dict`      | ⚠️ Partial          | Elements wrapped in single-element vectors; round-trip may alter type |
| Python `None` / `pd.NA`                        | ✅ High              | Converted to R `NULL`                                                 |

# Guidance

- Typical workflows (DataFrames, numeric arrays, series, homogeneous lists) are fully supported.
- Rare or highly heterogeneous Python objects may not round-trip perfectly.
- Round-trip fidelity is mainly a “nice-to-have” for debugging. For production pipelines, it’s safe to focus on supported types.

---

## Examples

### Basic — run a local R script

```python
from pathlib import Path
from rpy_bridge import RFunctionCaller

project_dir = Path("/path/to/your-r-project")
script = project_dir / "scripts" / "example.R"

caller = RFunctionCaller(path_to_renv=project_dir, script_path=script)
result = caller.call("some_function", 42, named_arg="value")
print(type(result))
```

### Call installed R packages (no local script)

```python
from rpy_bridge import RFunctionCaller

caller = RFunctionCaller(path_to_renv=None, packages=["stats"])
samples = caller.call("rnorm", 5, mean=10)
print(type(samples))  # typically a numpy.ndarray

median_val = caller.call("stats::median", samples)
print(median_val)
```

---

## R Setup

If you plan to execute R code with `rpy-bridge`, use the helper scripts in
`examples/r-deps/` to prepare an R environment.

- On macOS (Homebrew) install system deps:

```bash
bash examples/r-deps/install_r_dev_deps_homebrew.sh
```

- Initialize a project `renv` (run in an R session):

```r
source("examples/r-deps/setup_env.R")
```

- Restore the environment on a new machine:

```r
renv::restore()
```

---

## Collaboration note

This repository provides example R setup scripts for teams working across Python and R. Each project may require different R packages — check the package list in `examples/r-deps/setup_env.R` and commit a `renv.lock` for project-specific reproducibility.

Clone repositories containing R scripts locally or use your preferred tooling to obtain scripts before execution.

---

## Licensing

- `rpy-bridge` is released under the MIT License © 2025 Victoria Cheung.
- The project depends on [`rpy2`](https://rpy2.github.io) which is licensed under the GNU General Public License v2 (or later).

### Thanks

This package was spun out of internal tooling at Revolution Medicines.
Many thanks to the team there for allowing the code to be open sourced.
