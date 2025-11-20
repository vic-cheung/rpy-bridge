# rpy-bridge

Utilities for calling R code from Python using `rpy2`, including helpers to
activate `renv` projects, invoke R functions, and post-process results into
well-typed pandas DataFrames.

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

Token discovery and `require_token`

`rpy-bridge` will attempt to discover a GitHub token automatically when you
call `RFunctionCaller.from_github(...)` or `call_r_function_from_github(...)`:

- It first checks `GITHUB_TOKEN` and `GH_TOKEN` environment variables.
- If those are unset, it will query the git credential helper (same as
  `git credential fill`).

If you need to ensure authenticated access (for private repos), pass
`require_token=True` to have the call fail fast with a clear error message
when no token is available.

Example (private repo)

```python
from rpy_bridge import call_r_function_from_github

# This will raise immediately if no token is available (env var or git creds)
result = call_r_function_from_github(
  repo="your-org/private-repo",
  file_path="scripts/private_script.R",
  function_name="do_secret_thing",
  require_token=True,
)
```

## Licensing

- `rpy-bridge` is released under the MIT License © 2025 Victoria Cheung.
- The project depends on [`rpy2`](https://rpy2.github.io) which is licensed
  under the GNU General Public License v2 (or later). Distributing binaries that
  bundle `rpy2` must comply with the GPL terms. When you install `rpy-bridge`
  as a dependency, `rpy2` is resolved directly from its upstream maintainers.

### Thanks

This package was spun out of internal tooling at Revolution Medicines. Many
thanks to the team there for allowing the code to be open sourced.
