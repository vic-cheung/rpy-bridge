"""
Wrapper for calling R functions from Python using rpy2.

----------
** R must be installed and accessible in your environment **
Ensure compatibility with your R project's renv setup (or other virtual env/base env if that's what you're using).
----------
"""

# ruff: noqa: E402
# %%
# Import libraries
import importlib.util
import os
import subprocess
import sys
import warnings
from pathlib import Path
from typing import TYPE_CHECKING, Any, Union

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore", message="Environment variable .* redefined by R")


if TYPE_CHECKING:
    import logging as logging_module

    from loguru import Logger as LoguruLogger

    LoggerType = LoggerType = Union[LoguruLogger, logging_module.Logger]
else:
    LoggerType = None  # runtime doesn’t need the type object

import logging

try:
    from loguru import logger as loguru_logger  # type: ignore

    logger = loguru_logger
except ImportError:
    logging.basicConfig()
    logger = logging.getLogger("rpy-bridge")


# ---------------------------------------------------------------------
# R detection and rpy2 installation
# ---------------------------------------------------------------------
def ensure_rpy2_available() -> None:
    """
    Ensure rpy2 is importable.
    Do NOT attempt to install dynamically; fail with clear instructions instead.
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
        if r_home.endswith(">"):  # sometimes R console prints >
            r_home = r_home[:-1].strip()
        return r_home
    except FileNotFoundError:
        # fallback paths (Linux, macOS Homebrew, Windows)
        possible_paths = [
            "/usr/lib/R",
            "/usr/local/lib/R",
            "/opt/homebrew/Cellar/r/4.5.2/lib/R",  # macOS Homebrew
            "C:\\Program Files\\R\\R-4.5.2",  # Windows
        ]
        for p in possible_paths:
            if os.path.exists(p):
                return p
    return None


R_HOME = find_r_home()
if not R_HOME:
    raise RuntimeError("R not found. Please install R or add it to PATH.")

logger.info(f"R_HOME = {R_HOME}")
os.environ["R_HOME"] = R_HOME
ensure_rpy2_available()

# macOS dynamic library path
if sys.platform == "darwin":
    lib_path = os.path.join(R_HOME, "lib")
    if lib_path not in os.environ.get("DYLD_FALLBACK_LIBRARY_PATH", ""):
        os.environ["DYLD_FALLBACK_LIBRARY_PATH"] = (
            f"{lib_path}:{os.environ.get('DYLD_FALLBACK_LIBRARY_PATH','')}"
        )

elif sys.platform.startswith("linux"):
    lib_path = os.path.join(R_HOME, "lib")
    ld_path = os.environ.get("LD_LIBRARY_PATH", "")
    os.environ["LD_LIBRARY_PATH"] = f"{lib_path}:{ld_path}"

# ---------------------------------------------------------------------
# Lazy rpy2 import machinery
# ---------------------------------------------------------------------
_RPY2: dict | None = None


def _require_rpy2(raise_on_missing: bool = True) -> dict | None:
    global _RPY2
    if _RPY2 is not None:
        return _RPY2

    try:
        import rpy2.robjects as ro
        from rpy2 import robjects
        from rpy2.rinterface_lib.sexp import NULLType
        from rpy2.rlike.container import NamedList
        from rpy2.robjects import pandas2ri
        from rpy2.robjects.conversion import localconverter
        from rpy2.robjects.vectors import (
            BoolVector,
            FloatVector,
            IntVector,
            ListVector,
            StrVector,
        )

        _RPY2 = {
            "ro": ro,
            "robjects": robjects,
            "pandas2ri": pandas2ri,
            "localconverter": localconverter,
            "BoolVector": BoolVector,
            "FloatVector": FloatVector,
            "IntVector": IntVector,
            "ListVector": ListVector,
            "StrVector": StrVector,
            "NULLType": NULLType,
            "NamedList": NamedList,
        }
        return _RPY2

    except ImportError as e:
        if raise_on_missing:
            raise RuntimeError(
                "R support requires optional dependency `rpy2`. Install with: pip install rpy-bridge[r]"
            ) from e
        return None


def _ensure_rpy2() -> dict:
    global _RPY2
    if _RPY2 is None:
        _RPY2 = _require_rpy2()
    assert _RPY2 is not None, "_require_rpy2() returned None"
    return _RPY2


# ---------------------------------------------------------------------
# Activate renv
# ---------------------------------------------------------------------
def activate_renv(path_to_renv: Path) -> None:
    r = _ensure_rpy2()
    robjects = r["robjects"]

    path_to_renv = path_to_renv.resolve()
    if path_to_renv.name == "renv" and (path_to_renv / "activate.R").exists():
        renv_dir = path_to_renv
        project_dir = path_to_renv.parent
    else:
        renv_dir = path_to_renv / "renv"
        project_dir = path_to_renv

    renv_activate = renv_dir / "activate.R"
    renv_lock = project_dir / "renv.lock"

    if not renv_activate.exists() or not renv_lock.exists():
        raise FileNotFoundError(f"[Error] renv environment incomplete: {path_to_renv}")

    renviron_file = project_dir / ".Renviron"
    if renviron_file.is_file():
        os.environ["R_ENVIRON_USER"] = str(renviron_file)
        logger.info(f"R_ENVIRON_USER set to: {renviron_file}")

    rprofile_file = project_dir / ".Rprofile"
    if rprofile_file.is_file():
        robjects.r(f'source("{rprofile_file.as_posix()}")')
        logger.info(f".Rprofile sourced: {rprofile_file}")

    try:
        robjects.r("suppressMessages(library(renv))")
    except Exception:
        logger.info("Installing renv package in project library...")
        robjects.r(
            f'install.packages("renv", repos="https://cloud.r-project.org", lib="{renv_dir / "library"}")'
        )
        robjects.r("library(renv)")

    robjects.r(f'renv::load("{project_dir.as_posix()}")')
    logger.info(f"renv environment loaded for project: {project_dir}")


# ---------------------------------------------------------------------
# RFunctionCaller
# ---------------------------------------------------------------------
class RFunctionCaller:
    """
    Utility to load and call R functions from a script, lazily loading rpy2 and activating renv.

    Supports:
    - Scripts with custom functions
    - Base R functions
    - Functions in installed packages
    - Automatic conversion of Python types (lists, dicts, scalars, pandas DataFrames) to R objects
    """

    def __init__(
        self,
        path_to_renv: Path | None = None,
        script_path: Path | None = None,
        packages: list[str] | None = None,
    ):
        self.path_to_renv = path_to_renv.resolve() if path_to_renv else None
        self.script_path = script_path.resolve() if script_path else None
        self.packages = packages or None

        # Lazy-loaded attributes
        self._r = None
        self.ro = None
        self.robjects = None
        self.pandas2ri = None
        self.localconverter = None
        self.IntVector = None
        self.FloatVector = None
        self.BoolVector = None
        self.StrVector = None
        self.ListVector = None
        self.NamedList = None

        if self.script_path and not self.script_path.exists():
            raise FileNotFoundError(f"R script not found: {self.script_path}")

        self.script_dir = self.script_path.parent if self.script_path else None
        self._script_loaded = False
        self._renv_activated = False
        self._packages_loaded = False

    # -----------------------------------------------------------------
    # Internal: lazy R loading
    # -----------------------------------------------------------------
    def _ensure_r_loaded(self):
        if self._r is None:
            r = _require_rpy2(raise_on_missing=True)
            self._r = r
            self.ro = r["ro"]
            self.robjects = r["robjects"]
            self.pandas2ri = r["pandas2ri"]
            self.localconverter = r["localconverter"]
            self.IntVector = r["IntVector"]
            self.FloatVector = r["FloatVector"]
            self.BoolVector = r["BoolVector"]
            self.StrVector = r["StrVector"]
            self.ListVector = r["ListVector"]
            self.NamedList = r["NamedList"]

        # Activate renv
        if self.path_to_renv and not self._renv_activated:
            activate_renv(self.path_to_renv)
            self._renv_activated = True

        # Load packages
        if self.packages and not self._packages_loaded:
            for pkg in self.packages:
                try:
                    self.robjects.r(f'suppressMessages(library("{pkg}"))')
                except Exception:
                    logger.info(f"Package '{pkg}' not found. Installing...")
                    self.robjects.r(
                        f'install.packages("{pkg}", repos="https://cloud.r-project.org")'
                    )
                    self.robjects.r(f'suppressMessages(library("{pkg}"))')
            self._packages_loaded = True

        # Source script
        if self.script_path and not self._script_loaded:
            self.robjects.r(f'setwd("{self.script_dir.as_posix()}")')
            self.robjects.r(f'source("{self.script_path.as_posix()}")')
            logger.info(f"R script sourced: {self.script_path.name}")
            self._script_loaded = True

    def _clean_scalar(self, x):
        """
        Clean R-style missing values to pandas/NumPy equivalents.
        Called inside _r2py on each vector element; atomic/scalar only.
        """
        r = self._r
        ro = r["robjects"]

        if x is None:
            return None

        if x in (
            getattr(ro, "NA_Real", None),
            getattr(ro, "NA_Integer", None),
            getattr(ro, "NA_Logical", None),
        ):
            return None

        if x is getattr(ro, "NA_Character", None):
            return None

        if isinstance(x, float) and np.isnan(x):
            return None

        return x

    # -----------------------------------------------------------------
    # Python -> R conversion
    # -----------------------------------------------------------------
    def _py2r(self, obj):
        """
        Convert Python objects to R objects robustly.
        Handles scalars, None/pd.NA, lists, dicts, and pandas DataFrames.
        """
        self._ensure_r_loaded()
        robjects = self.robjects
        pandas2ri = self.pandas2ri
        FloatVector = self.FloatVector
        BoolVector = self.BoolVector
        StrVector = self.StrVector
        ListVector = self.ListVector
        localconverter = self.localconverter
        import pandas as pd
        import rpy2.robjects.vectors as rvec

        # Pass through existing R objects
        if isinstance(
            obj,
            (
                rvec.IntVector,
                rvec.FloatVector,
                rvec.BoolVector,
                rvec.StrVector,
                rvec.ListVector,
                robjects.DataFrame,
            ),
        ):
            return obj

        with localconverter(robjects.default_converter + pandas2ri.converter):
            if obj is None or obj is pd.NA:
                return robjects.NULL

            # DataFrame → data.frame
            if isinstance(obj, pd.DataFrame):
                return pandas2ri.py2rpy(obj)

            # Series → vector
            if isinstance(obj, pd.Series):
                return self._py2r(obj.tolist())

            # Scalars
            if isinstance(obj, (int, float, bool, str)):
                return obj

            # Lists
            if isinstance(obj, list):
                if len(obj) == 0:
                    return FloatVector([])
                elif all(isinstance(x, (int, float)) or x is None for x in obj):
                    return FloatVector(
                        [robjects.NA_Real if x is None else float(x) for x in obj]
                    )

                def is_na(x):
                    return (
                        x is None or x is pd.NA or (isinstance(x, float) and pd.isna(x))
                    )

                # Homogeneous numeric
                if all(
                    isinstance(x, (int, float)) and not isinstance(x, bool) or is_na(x)
                    for x in obj
                ):
                    return FloatVector(
                        [robjects.NA_Real if is_na(x) else float(x) for x in obj]
                    )

                # Homogeneous bool
                if all(isinstance(x, bool) or is_na(x) for x in obj):
                    return BoolVector(
                        [robjects.NA_Logical if is_na(x) else x for x in obj]
                    )

                # Homogeneous str
                if all(isinstance(x, str) or is_na(x) for x in obj):
                    return StrVector(
                        [robjects.NA_Character if is_na(x) else x for x in obj]
                    )

                # Mixed or nested list → ListVector with positional keys
                return ListVector({str(i): self._py2r(v) for i, v in enumerate(obj)})

            # Dict → NamedList
            if isinstance(obj, dict):
                return ListVector({k: self._py2r(v) for k, v in obj.items()})

            raise NotImplementedError(f"Cannot convert Python object to R: {type(obj)}")

    # -----------------------------------------------------------------
    # R -> Python conversion
    # -----------------------------------------------------------------
    def _r2py(self, obj, top_level=True):
        """
        Convert R objects to Python objects robustly.
        Handles DataFrames, NamedList/ListVector, atomic vectors, and NULL.
        """
        r = self._r
        robjects = self.robjects
        NamedList = self.NamedList
        ListVector = self.ListVector
        StrVector = self.StrVector
        IntVector = self.IntVector
        FloatVector = self.FloatVector
        BoolVector = self.BoolVector
        NULLType = r["NULLType"]
        lc = self.localconverter
        pandas2ri = self.pandas2ri

        if isinstance(obj, NULLType):
            return None

        if isinstance(obj, robjects.DataFrame):
            with lc(robjects.default_converter + pandas2ri.converter):
                df = robjects.conversion.rpy2py(obj)
            df = postprocess_r_dataframe(df)
            df = clean_r_missing(df, caller=self)
            return df

        if isinstance(obj, (NamedList, ListVector)):
            py_obj = r_namedlist_to_dict(obj, caller=self, top_level=top_level)
            # Auto-unpack single-element lists only at top-level
            if isinstance(py_obj, list) and len(py_obj) == 1 and top_level:
                return py_obj[0]
            return py_obj

        if isinstance(obj, (StrVector, IntVector, FloatVector, BoolVector)):
            py_list = [self._clean_scalar(v) for v in obj]
            if len(py_list) == 1 and top_level:
                return py_list[0]
            return py_list

        return self._clean_scalar(obj)

    # -----------------------------------------------------------------
    # Public: ensure R package is available
    # -----------------------------------------------------------------
    def ensure_r_package(self, pkg_name: str):
        r = self.robjects.r
        try:
            r(f'suppressMessages(library("{pkg_name}", character.only=TRUE))')
        except Exception:
            r(f'install.packages("{pkg_name}", repos="https://cloud.r-project.org")')
            r(f'suppressMessages(library("{pkg_name}", character.only=TRUE))')

    # -----------------------------------------------------------------
    # Public: call an R function
    # -----------------------------------------------------------------
    def call(self, func_name: str, *args, **kwargs):
        """
        Call an R function safely. Supports:
        - functions defined in scripts
        - base R functions
        - functions in loaded packages
        """
        self._ensure_r_loaded()

        # --- Find the function ---
        func = None
        try:
            func = self.robjects.globalenv[func_name]  # script-defined
        except KeyError:
            try:
                func = self.robjects.r[func_name]  # base or package function
            except KeyError:
                # --- Added: handle namespaced functions like stats::median ---
                if "::" in func_name:
                    pkg, fname = func_name.split("::", 1)
                    try:
                        func = self.robjects.r(f"{pkg}::{fname}")
                    except Exception as e:
                        raise RuntimeError(
                            f"Failed to load R function '{func_name}' via namespace: {e}"
                        ) from e

                if func is None:
                    raise ValueError(f"R function '{func_name}' not found.")

        # --- Convert Python args to R ---
        r_args = [self._py2r(a) for a in args]
        r_kwargs = {k: self._py2r(v) for k, v in kwargs.items()}

        # --- Call safely ---
        try:
            result = func(*r_args, **r_kwargs)
        except Exception as e:
            raise RuntimeError(f"Error calling R function '{func_name}': {e}")

        # --- Convert R result back to Python ---
        return self._r2py(result)


# %%
# ------------------------------
# Utility functions for R ↔ Python
# ------------------------------
def r_namedlist_to_dict(namedlist, caller: RFunctionCaller, top_level=False):
    """
    Recursively convert an R NamedList or ListVector to a Python dictionary.
    Uses the caller._r2py method for nested conversions.
    """
    r = _ensure_rpy2()
    NamedList = r["NamedList"]
    ListVector = r["ListVector"]

    if isinstance(namedlist, (NamedList, ListVector)):
        names = namedlist.names if not callable(namedlist.names) else namedlist.names()

        # Detect positional (unnamed) list
        if names and all(str(i) == str(name) for i, name in enumerate(names)):
            out = []
            for v in namedlist:
                # Nested elements are never top-level
                val = caller._r2py(v, top_level=False)
                out.append(val)
            return out

        # Otherwise dict
        result = {}
        for i, val in enumerate(namedlist):
            key = names[i] if names and i < len(names) else str(i)
            v_py = caller._r2py(val, top_level=False)  # nested elements
            result[str(key)] = v_py
        return result

    # Fallback: scalar/vector at the very top
    return caller._r2py(namedlist, top_level=top_level)


def clean_r_dataframe(r_df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean an R data.frame by removing non-structural attributes like .groups and .rows.
    """
    for attr in [".groups", ".rows"]:
        try:
            del r_df.attrs[attr]
        except (KeyError, AttributeError):
            pass
    return r_df


def fix_string_nans(df: pd.DataFrame) -> pd.DataFrame:
    """
    Replace string NAs or empty strings with pd.NA.
    """
    return df.replace(["nan", "NaN", "NA", "na", ""], pd.NA)


def normalize_single_df_dtypes(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normalize dtypes in a single DataFrame after R conversion.
    """
    df = df.replace(["", "nan", "NaN", "NA", "na"], pd.NA)

    for col in df.columns:
        series = df[col]
        if pd.api.types.is_object_dtype(series):
            coerced = pd.to_numeric(series, errors="coerce")
            if coerced.notna().sum() >= series.notna().sum() * 0.5:
                df[col] = coerced
        if pd.api.types.is_integer_dtype(df[col]) and df[col].isna().any():
            df[col] = df[col].astype("float64")
    return df


def fix_r_dataframe_types(df: pd.DataFrame) -> pd.DataFrame:
    """
    Post-process R DataFrame:
    - Convert R NA_integer_ sentinel (-2147483648) to pd.NA
    - Convert R-style numeric dates to datetime
    - Remove timezone from datetime columns
    """
    for col in df.columns:
        series = df[col]

        if pd.api.types.is_integer_dtype(series):
            df[col] = series.mask(series == -2147483648, pd.NA)

        if pd.api.types.is_numeric_dtype(series):
            values = series.dropna()
            if not values.empty and values.between(10000, 40000).all():
                try:
                    df[col] = pd.to_datetime("1970-01-01") + pd.to_timedelta(
                        series, unit="D"
                    )
                except Exception:
                    pass

        if pd.api.types.is_datetime64tz_dtype(series):
            df[col] = series.dt.tz_localize(None)

    return df


def postprocess_r_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply a series of fixes to a DataFrame converted from R:
    - Type corrections
    - String NA normalization
    - Index normalization
    """
    df = fix_r_dataframe_types(df)
    df = fix_string_nans(df)
    df = normalize_single_df_dtypes(df)

    if df.index.dtype == object:
        try:
            int_index = df.index.astype(int)
            if (int_index == np.arange(len(df)) + 1).all():
                df.index = pd.RangeIndex(start=0, stop=len(df))
        except Exception:
            pass
    return df


def clean_r_missing(obj, caller: RFunctionCaller):
    """
    Post-process R return objects for downstream Python use.
    Recursively convert R-style missing values to pandas/NumPy:
    - NA_integer_, NA_real_, NA_logical_ → np.nan
    - NA_character_ → pd.NA
    """
    r = _ensure_rpy2()
    ro = r["robjects"]

    NA_MAP = {
        getattr(ro, "NA_Real", None): np.nan,
        getattr(ro, "NA_Integer", None): np.nan,
        getattr(ro, "NA_Logical", None): np.nan,
        getattr(ro, "NA_Character", None): pd.NA,
    }

    if isinstance(obj, pd.DataFrame):
        for col in obj.columns:
            obj[col] = obj[col].apply(lambda x: clean_r_missing(x, caller))
        return obj

    elif isinstance(obj, dict):
        return {k: clean_r_missing(v, caller) for k, v in obj.items()}

    elif isinstance(obj, list):
        return [clean_r_missing(v, caller) for v in obj]

    else:
        return NA_MAP.get(obj, obj)


# %%
# -------------------------------------------
# Functions here onwards are utility functions
# for comparing R and Python DataFrames.
# -------------------------------------------


def normalize_dtypes(
    df1: pd.DataFrame, df2: pd.DataFrame
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Aligns column dtypes across two DataFrames for accurate comparison.
    - Replaces empty strings with pd.NA.
    - Attempts to coerce strings to numeric where applicable.
    - Aligns dtypes between matching columns (e.g. float64 vs int64).
    """
    for col in df1.columns.intersection(df2.columns):
        # Replace empty strings with NA
        df1[col] = df1[col].replace("", pd.NA)
        df2[col] = df2[col].replace("", pd.NA)

        s1, s2 = df1[col], df2[col]
        dtype1, dtype2 = s1.dtype, s2.dtype

        # If one is numeric and the other is object, try coercing both to numeric
        if (
            pd.api.types.is_numeric_dtype(dtype1)
            and pd.api.types.is_object_dtype(dtype2)
        ) or (
            pd.api.types.is_object_dtype(dtype1)
            and pd.api.types.is_numeric_dtype(dtype2)
        ):
            try:
                df1[col] = pd.to_numeric(s1, errors="coerce")
                df2[col] = pd.to_numeric(s2, errors="coerce")
                continue  # skip to next column if coercion succeeds
            except Exception:
                pass  # fallback to next block if coercion fails

        # If both are numeric but of different types (e.g., int vs float), unify to float64
        if pd.api.types.is_numeric_dtype(dtype1) and pd.api.types.is_numeric_dtype(
            dtype2
        ):
            df1[col] = df1[col].astype("float64")
            df2[col] = df2[col].astype("float64")
            continue

        # If both are objects or strings, convert both to str for equality comparison
        if pd.api.types.is_object_dtype(dtype1) or pd.api.types.is_object_dtype(dtype2):
            df1[col] = df1[col].astype(str)
            df2[col] = df2[col].astype(str)

    return df1, df2


# %%
def align_numeric_dtypes(
    df1: pd.DataFrame, df2: pd.DataFrame
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Ensure aligned numeric dtypes between two DataFrames for accurate comparison.
    Converts between int, float, and numeric-looking strings where appropriate.
    Also handles NA and empty string normalization.
    """
    for col in df1.columns.intersection(df2.columns):
        s1, s2 = df1[col], df2[col]

        # Replace empty strings with NA to avoid type promotion issues
        s1 = s1.replace("", pd.NA)
        s2 = s2.replace("", pd.NA)

        # Try to coerce both to numeric (non-destructive)
        try:
            s1_num = pd.to_numeric(s1, errors="coerce")
            s2_num = pd.to_numeric(s2, errors="coerce")

            # If at least one successfully converts and it's not all NaN
            if not s1_num.isna().all() or not s2_num.isna().all():
                df1[col] = s1_num.astype("float64")
                df2[col] = s2_num.astype("float64")
                continue  # move to next column
        except Exception:
            pass

        # Otherwise, fall back to original values
        df1[col] = s1
        df2[col] = s2

    return df1, df2


# %%
def compare_r_py_dataframes(
    df1: pd.DataFrame, df2: pd.DataFrame, float_tol: float = 1e-8
) -> dict:
    """
    Compare a Python DataFrame (df1) with an R DataFrame converted to pandas (df2).

    Returns:
        dict with mismatch diagnostics, preserving original indices in diffs.
    """

    results: dict[str, Any] = {
        "shape_mismatch": False,
        "columns_mismatch": False,
        "index_mismatch": False,
        "numeric_diffs": {},  # type: dict[str, pd.DataFrame]
        "non_numeric_diffs": {},  # type: dict[str, pd.DataFrame]
    }

    # --- Preprocessing: fix R-specific issues ---
    df2 = fix_r_dataframe_types(df2)

    # --- Replace common string NAs with proper pd.NA ---
    df1 = fix_string_nans(df1)
    df2 = fix_string_nans(df2)

    # --- Normalize and align dtypes ---
    df1, df2 = normalize_dtypes(df1.copy(), df2.copy())
    df1, df2 = align_numeric_dtypes(df1, df2)

    # --- Check shape ---
    if df1.shape != df2.shape:
        results["shape_mismatch"] = True
        print(f"[Warning] Shape mismatch: df1 {df1.shape} vs df2 {df2.shape}")

    # --- Check columns ---
    if set(df1.columns) != set(df2.columns):
        results["columns_mismatch"] = True
        print("[Warning] Column mismatch:")
        print(f"  df1: {df1.columns}")
        print(f"  df2: {df2.columns}")
        common_cols = df1.columns.intersection(df2.columns)
    else:
        common_cols = df1.columns

    # --- Ensure columns are the same order ---
    df1_aligned = df1.loc[:, common_cols]
    df2_aligned = df2.loc[:, common_cols]

    # --- Compare values column by column ---
    for col in common_cols:
        col_py = df1_aligned[col]
        col_r = df2_aligned[col]

        if pd.api.types.is_numeric_dtype(col_py) and pd.api.types.is_numeric_dtype(
            col_r
        ):
            col_py, col_r = col_py.align(col_r)

            close = np.isclose(
                col_py.fillna(np.nan),
                col_r.fillna(np.nan),
                atol=float_tol,
                equal_nan=True,
            )
            if not close.all():
                diffs = pd.DataFrame(
                    {
                        "df1": col_py[~close],
                        "df2": col_r[~close],
                    }
                )
                results["numeric_diffs"][col] = diffs

        else:
            # Treat missing values as equal: create mask where values differ excluding matching NAs
            unequal = ~col_py.eq(col_r)
            both_na = col_py.isna() & col_r.isna()
            unequal = unequal & ~both_na

            if unequal.any():
                diffs = pd.DataFrame(
                    {
                        "df1": col_py[unequal],
                        "df2": col_r[unequal],
                    }
                )
                results["non_numeric_diffs"][col] = diffs

    return results


# %%
