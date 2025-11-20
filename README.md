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

Using a script fetched from GitHub (safe defaults)

```python
from rpy_bridge import call_r_function_from_github

# This only executes the remote code when `trust_remote_code=True`.
# When False the call returns a cached Path to the downloaded script.
path = call_r_function_from_github(
    repo="some-owner/some-repo",
    file_path="scripts/analysis.R",
    function_name="analyse",
    trust_remote_code=False,  # inspect file before running
)

print("Cached script at:", path)
```

To execute remote code explicitly (opt-in):

```python
from rpy_bridge import call_r_function_from_github

# Only set trust_remote_code=True after you've reviewed the script.
result = call_r_function_from_github(
    repo="some-owner/some-repo",
    file_path="scripts/analysis.R",
    function_name="analyse",
    trust_remote_code=True,
    require_token=False,  # set True for private repos
)
```

Security & token notes

- `require_token=True` causes the fetch to fail fast if no token is available.
- When `require_token=True` and a token is not found, `rpy-bridge` will prompt
  interactively (TTY) to paste a token; set `prompt=False` to disable prompting.
- Prefer providing `GITHUB_TOKEN` as an env var in CI for non-interactive runs.

Caching

- Downloaded scripts are cached under `~/.cache/rpy-bridge` and keyed by
  repository and commit SHA so repeated fetches are fast and reproducible.



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
