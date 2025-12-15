"""
Environment discovery for R and rpy2.

Responsible for:
- warning suppression for benign R env messages
- detecting the R installation and exporting R_HOME
- platform-specific library path adjustments
- CI/testing skip knobs
- availability check for rpy2

Importing this module performs the same side effects as the original
rpy2_utils import-time block to avoid behavior changes.
"""

from __future__ import annotations

import importlib.util
import os
import subprocess
import sys
import warnings

from .logging import logger

warnings.filterwarnings("ignore", message="Environment variable .* redefined by R")

# Determine if we're running in CI / testing
CI_TESTING = os.environ.get("GITHUB_ACTIONS") == "true" or os.environ.get("TESTING") == "1"


def ensure_rpy2_available() -> None:
    """
    Raise with instructions if rpy2 is missing.
    """
    if importlib.util.find_spec("rpy2") is None:
        raise RuntimeError(
            "\n[Error] rpy2 is not installed. Please install it in your Python environment:\n"
            "  pip install rpy2\n\n"
            "Make sure your Python environment can access your system R installation.\n"
            "On macOS with Homebrew: brew install r\n"
            "On Linux: apt install r-base  (Debian/Ubuntu) or yum install R (CentOS/RHEL)\n"
            "On Windows: install R from https://cran.r-project.org\n"
        )


def find_r_home() -> str | None:
    """Detect system R installation."""
    try:
        r_home = subprocess.check_output(
            ["R", "--vanilla", "--slave", "-e", "cat(R.home())"],
            stderr=subprocess.PIPE,
            text=True,
        ).strip()
        if r_home.endswith(">"):
            r_home = r_home[:-1].strip()
        return r_home
    except FileNotFoundError:
        possible_paths = [
            "/usr/lib/R",
            "/usr/local/lib/R",
            "/opt/homebrew/Cellar/r/4.5.2/lib/R",
            "C:\\Program Files\\R\\R-4.5.2",
        ]
        for path in possible_paths:
            if os.path.exists(path):
                return path
    return None


R_HOME = os.environ.get("R_HOME")
if not R_HOME:
    R_HOME = find_r_home()
    if not R_HOME:
        if CI_TESTING:
            logger.warning("R not found; skipping all R-dependent setup in CI/testing environment.")
            R_HOME = None
        else:
            raise RuntimeError("R not found. Please install R or add it to PATH.")
    else:
        os.environ["R_HOME"] = R_HOME

logger.info(
    f"[rpy-bridge] R_HOME = {R_HOME if R_HOME else 'not detected; R-dependent code skipped'}"
)

# Only configure platform-specific library paths if R is available
if R_HOME:
    if sys.platform == "darwin":
        lib_path = os.path.join(R_HOME, "lib")
        if lib_path not in os.environ.get("DYLD_FALLBACK_LIBRARY_PATH", ""):
            os.environ["DYLD_FALLBACK_LIBRARY_PATH"] = (
                f"{lib_path}:{os.environ.get('DYLD_FALLBACK_LIBRARY_PATH', '')}"
            )

    elif sys.platform.startswith("linux"):
        lib_path = os.path.join(R_HOME, "lib")
        ld_path = os.environ.get("LD_LIBRARY_PATH", "")
        if lib_path not in ld_path.split(":"):
            os.environ["LD_LIBRARY_PATH"] = f"{lib_path}:{ld_path}"

    elif sys.platform.startswith("win"):
        bin_path = os.path.join(R_HOME, "bin", "x64")
        path_env = os.environ.get("PATH", "")
        if bin_path not in path_env.split(os.pathsep):
            os.environ["PATH"] = f"{bin_path}{os.pathsep}{path_env}"


__all__ = ["CI_TESTING", "R_HOME", "ensure_rpy2_available", "find_r_home"]
