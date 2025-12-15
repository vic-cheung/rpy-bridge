"""
Helpers for locating project roots and activating renv environments.

These utilities are shared by RFunctionCaller and exposed for compatibility.
"""

from __future__ import annotations

import os
from pathlib import Path

from .logging import logger
from .rpy2_loader import ensure_rpy2


def normalize_scripts(scripts: str | Path | list[str | Path] | None) -> list[Path]:
    """
    Normalize script inputs to a list of resolved Paths.
    """
    if scripts is None:
        return []
    if isinstance(scripts, (str, Path)):
        return [Path(scripts).resolve()]
    try:
        return [Path(s).resolve() for s in scripts]
    except TypeError as exc:
        raise TypeError(
            f"Invalid type for 'scripts': {type(scripts)}. Must be str, Path, or list/iterable thereof."
        ) from exc


def candidate_project_dirs(base: Path, depth: int = 3) -> list[Path]:
    return [base] + list(base.parents)[:depth]


def has_root_marker(path: Path) -> bool:
    if (path / ".git").exists():
        return True
    if any(path.glob("*.Rproj")):
        return True
    if (path / ".here").exists():
        return True
    if (path / "DESCRIPTION").exists():
        return True
    if (path / "renv.lock").exists():
        return True
    return False


def find_project_root(path_to_renv: Path | None, scripts: list[Path]) -> Path | None:
    bases: list[Path] = []
    if scripts:
        bases.extend(candidate_project_dirs(scripts[0].parent))
    if path_to_renv is not None:
        bases.extend(candidate_project_dirs(path_to_renv))

    seen = set()
    for cand in bases:
        resolved = cand.resolve()
        if resolved in seen:
            continue
        seen.add(resolved)
        if has_root_marker(resolved):
            return resolved
    return None


def activate_renv(path_to_renv: Path) -> None:
    r = ensure_rpy2()
    robjects = r["robjects"]

    path_to_renv = Path(path_to_renv).resolve()

    def _candidates(base: Path) -> list[Path]:
        return [base] + list(base.parents)[:3]

    project_dir = None
    renv_dir = None
    renv_activate = None
    renv_lock = None

    for cand in _candidates(path_to_renv):
        cand_is_renv = cand.name == "renv" and (cand / "activate.R").exists()
        if cand_is_renv:
            rd = cand
            pd = cand.parent
        else:
            rd = cand / "renv"
            pd = cand

        activate_path = rd / "activate.R"
        lock_path = pd / "renv.lock"
        if not lock_path.exists():
            alt_lock = rd / "renv.lock"
            if alt_lock.exists():
                lock_path = alt_lock

        if activate_path.exists() and lock_path.exists():
            project_dir = pd
            renv_dir = rd
            renv_activate = activate_path
            renv_lock = lock_path
            break

    if renv_dir is None or renv_activate is None or renv_lock is None:
        raise FileNotFoundError(
            f"[Error] renv environment incomplete: activate.R or renv.lock not found near {path_to_renv}"
        )

    renviron_file = project_dir / ".Renviron"
    if renviron_file.is_file():
        os.environ["R_ENVIRON_USER"] = str(renviron_file)
        logger.info(f"[rpy-bridge] R_ENVIRON_USER set to: {renviron_file}")

    rprofile_file = project_dir / ".Rprofile"
    if rprofile_file.is_file():
        try:
            robjects.r(
                f'old_wd <- getwd(); setwd("{project_dir.as_posix()}"); '
                f"on.exit(setwd(old_wd), add = TRUE); "
                f'source("{rprofile_file.as_posix()}")'
            )
            logger.info(f"[rpy-bridge] .Rprofile sourced: {rprofile_file}")
        except Exception as exc:  # pragma: no cover - defensive fallback
            logger.warning(
                "[rpy-bridge] Failed to source .Rprofile; falling back to renv::activate(): %s",
                exc,
            )

    try:
        robjects.r("suppressMessages(library(renv))")
    except Exception:
        logger.info("[rpy-bridge] Installing renv package in project library...")
        robjects.r(
            f'install.packages("renv", repos="https://cloud.r-project.org", lib="{renv_dir / "library"}")'
        )
        robjects.r("library(renv)")

    robjects.r(f'renv::load("{project_dir.as_posix()}")')
    logger.info(f"[rpy-bridge] renv environment loaded for project: {project_dir}")


__all__ = [
    "activate_renv",
    "normalize_scripts",
    "candidate_project_dirs",
    "has_root_marker",
    "find_project_root",
]
