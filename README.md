# rpy-bridge

Utilities for calling R code from Python using `rpy2`, including helpers to
activate `renv` projects, invoke R functions, and post-process results into
well-typed pandas DataFrames.

This project was developed for bilingual teams where some functions are
authored in R and the primary consumer is a Python-centric developer. It
acts as a lightweight interoperability layer enabling a Python programmer to
call and reuse R functions (written and maintained by R authors) without
rewriting them in Python.

## Installation

```bash
uv add rpy-bridge
```

The package requires:

- Python 3.12+
- `rpy2` (GPLv2 or later)
- `pandas`
- `numpy`

## Usage

```python
from pathlib import Path

from rpy_bridge import RFunctionCaller

caller = RFunctionCaller(
    path_to_renv=Path("/path/to/project"),
    script_path=Path("/path/to/script.R"),
)

summary_df = caller.call("summarize_cohort", cohort_df)


## Examples

Basic — run a local R script

```python
from pathlib import Path
from rpy_bridge import RFunctionCaller

# If your project uses renv, pass the project directory (parent of renv/)
project_dir = Path("/path/to/your-r-project")
script = project_dir / "scripts" / "example.R"

# If you do not use renv, pass None for path_to_renv
caller = RFunctionCaller(path_to_renv=project_dir, script_path=script)
result = caller.call("some_function", 42, named_arg="value")
print(type(result))
```

Notes:

- `path_to_renv` may be either the project directory (containing `renv/`) or
  the `renv/` directory itself. When provided, `rpy-bridge` will call
  `renv::load()` so the R session uses the project's library versions.

Remote fetch helpers were removed from this package to keep the API surface
small and avoid environment-specific SSL and token handling issues. The
intended workflow is:

- Clone or download the R script into your local filesystem (review the
  code if it came from a remote source).
- Construct an `RFunctionCaller` with `script_path` pointing to the local
  script and optionally `path_to_renv` to activate the project's R library.

This keeps network, token, and SSL concerns outside the package while
preserving an easy path for Python-first users to call R-written functions.

If you need to run an R script from a remote repository, clone the repository
locally (or download the script using your preferred tooling), review the
script if necessary, and then construct an `RFunctionCaller` with the local
`script_path`:

```python
from rpy_bridge import RFunctionCaller

project_dir = Path("/path/to/cloned/repo")
script = project_dir / "scripts" / "analysis.R"

caller = RFunctionCaller(path_to_renv=None, script_path=script)
result = caller.call("analyse", some_arg=42)
```



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

Review the scripts in `examples/r-deps/` before running; they install system
libraries and R packages and should be run from a trusted environment. For
CI, use `r-lib/actions/setup-r` to install R, then run the `Rscript` command
above to prepare the `renv` environment.

Collaboration note

This repository provides example R setup scripts for teams working across
Python and R. Each project may require different R packages — check the
package list in `examples/r-deps/setup_env.R` and commit a `renv.lock` for
project-specific reproducibility.

Note: Remote fetch helpers were intentionally removed; token discovery and
GitHub API interactions are no longer part of this package. Clone repositories
locally or use your preferred tooling to obtain scripts before execution.

## Licensing

- `rpy-bridge` is released under the MIT License © 2025 Victoria Cheung.
- The project depends on [`rpy2`](https://rpy2.github.io) which is licensed
  under the GNU General Public License v2 (or later). Distributing binaries that
  bundle `rpy2` must comply with the GPL terms. When you install `rpy-bridge`
  as a dependency, `rpy2` is resolved directly from its upstream maintainers.

### Thanks

This package was spun out of internal tooling at Revolution Medicines. Many
thanks to the team there for allowing the code to be open sourced.
