# R dependency helpers

This folder contains helper scripts to set up an R environment suitable for
running examples that call R via `rpy-bridge`.

Files:

- `install_r_dev_deps_homebrew.sh` — macOS/Homebrew helper to install system libs
- `setup_env.R` — initialize a project `renv` and install common R packages
- `setup_env_cluster.R` — variant suitable when using conda-managed R
- `.Rversion` — suggested R version used when developing these scripts

Usage

1. Install system dependencies (macOS)

```bash
bash examples/r-deps/install_r_dev_deps_homebrew.sh
```

Notes:

- The Homebrew script is macOS-specific — it installs system libraries that are
  commonly missing on macOS (font stacks, libjpeg, libtiff, etc.).

- On Linux you will typically use your distribution package manager (e.g.
  `apt`, `dnf`) to install the same libraries prior to installing R packages.

1. Initialize `renv` in the project directory (run in an R session)

```r
source("examples/r-deps/setup_env.R")
```

This will:

1. install `renv` if needed
1. initialize a project-local library and create `.Rprofile`
1. install the R packages listed in the script
1. create a `renv.lock` snapshot (useful to commit in examples if you want
   reproducible restores)

1. Restore on a new machine

```r
renv::restore()
```

CI example (GitHub Actions)

Add a job that installs R, runs system-setup if needed, and restores `renv`:

```yaml
jobs:
  renv:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Setup R
        uses: r-lib/actions/setup-r@v2
        with:
          r-version: '4.4.1'
      - name: Install system deps (optional)
        run: sudo apt-get update && sudo apt-get install -y libjpeg-dev libtiff-dev libfreetype6-dev
      - name: Restore R environment
        run: Rscript -e "renv::restore()"
```

Security & platform caveats

- Review `examples/r-deps/*` before running. The scripts install system
  libraries and packages from external repositories.
- Homebrew script is macOS-only. On Linux, adapt the package list to
  `apt`/`dnf`/etc. or use a container with R preinstalled.
- If your CI or cluster already provides R via conda or system packages,
  use `setup_env_cluster.R` (example) instead of the macOS script.

Collaboration & per-project dependencies

This folder contains example scripts and is intended as a starting point for
teams that mix Python and R work. Important notes:

- These are example dependency manifests and installer scripts — each project
  will have its own R package needs. Before running the setup scripts, check
  that the package list in `setup_env.R` matches your project's needs.
- If you're consuming R functions written by teammates, prefer keeping the R
  function definitions in the R project and call them through `rpy-bridge`.
  This keeps the R source and its dependencies co-located and easier to test.
- For reproducibility, commit a `renv.lock` from a known-working environment
  to your project repository and use `renv::restore()` on CI and new machines.


