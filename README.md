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
