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
import os
import warnings

warnings.filterwarnings("ignore", message="Environment variable .* redefined by R")

from pathlib import Path

import numpy as np
import pandas as pd
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
from typing import Optional

try:
    from loguru import logger  # type: ignore
except Exception:
    import logging

    logging.basicConfig()
    logger = logging.getLogger("rpy-bridge")


# %%
def activate_renv(path_to_renv: Path) -> None:
    """
    Activates the renv environment using renv::load() to ensure the correct project is loaded.
    This avoids sourcing activate.R directly and avoids accidentally initializing a new environment.

    Accepts either:
    - Direct path to renv directory (e.g., /path/to/renv)
    - Parent directory containing renv/ folder (e.g., /path/to/repos where renv/ is inside)
    """

    path_to_renv = path_to_renv.resolve()

    # Determine if path_to_renv is the renv directory itself or its parent
    if path_to_renv.name == "renv" and (path_to_renv / "activate.R").exists():
        # Path points directly to renv directory
        renv_dir = path_to_renv
        renv_project_dir = path_to_renv.parent
    else:
        # Path points to parent directory containing renv/
        renv_dir = path_to_renv / "renv"
        renv_project_dir = path_to_renv

    renv_activate = renv_dir / "activate.R"
    renv_lock = renv_project_dir / "renv.lock"

    if not renv_activate.exists() or not renv_lock.exists():
        raise FileNotFoundError(
            f"[Error] renv environment not found or incomplete.\n"
            f"  Expected activate.R at: {renv_activate}\n"
            f"  Expected renv.lock at: {renv_lock}\n"
            f"  Provided path: {path_to_renv}"
        )

    # Optional: set R_ENVIRON_USER if .Renviron exists
    renviron_file = renv_project_dir / ".Renviron"
    if renviron_file.is_file():
        os.environ["R_ENVIRON_USER"] = str(renviron_file)
        logger.info("R_ENVIRON_USER set to: {}", renviron_file)

    # Load the renv package
    try:
        robjects.r("library(renv)")
    except Exception:
        print("[Info] renv package not found in R. Attempting to install...")
        robjects.r('install.packages("renv", repos="https://cloud.r-project.org")')
        # Try loading again after installation
        robjects.r("library(renv)")

    # Load the renv environment using renv::load(path)
    try:
        logger.info("Using R at: {}", robjects.r("R.home()")[0])
        robjects.r(f'renv::load("{renv_project_dir.as_posix()}")')
        logger.info("renv environment loaded for project: {}", renv_project_dir)
    except Exception as e:
        raise RuntimeError(f"[Error] Failed to load renv environment: {e}")

    logger.debug(".libPaths(): {}", robjects.r(".libPaths()"))


# %%
class RFunctionCaller:
    """
    A utility class to load and execute R functions from a specified R script using rpy2.
    """

    def __init__(self, path_to_renv: Path | None, script_path: Path):
        """
        Initialize the RFunctionCaller with the path to the renv environment and the R script.
        Set path_to_renv to None if no renv is used.
        """
        if not script_path.exists():
            raise FileNotFoundError(f"R script not found: {script_path}")

        self.path_to_renv = path_to_renv.resolve() if path_to_renv else None

        self.script_path = script_path.resolve()
        self.script_dir = self.script_path.parent

        self._load_script()

    def _load_script(self):
        """
        Set the R working directory and source the R script.
        """
        if self.path_to_renv:
            activate_renv(self.path_to_renv)
        else:
            logger.info("No renv path provided; using base or current environment.")

        # Set the working directory to the script's directory
        robjects.r(f'setwd("{self.script_dir.as_posix()}")')
        robjects.r(f'source("{self.script_path.as_posix()}")')
        logger.info("R script sourced: {}", self.script_path.name)

    def call(self, function_name: str, *args: object, **kwargs: object) -> object:
        """
        Call an R function from the sourced script, and recursively convert &
        post-process the result.

        Handles:
        - Direct data.frame
        - NamedList or ListVector
        - Nested lists with data.frames inside
        """

        def _recursive_postprocess(obj):
            # Handle single DataFrame
            if isinstance(obj, pd.DataFrame):
                return postprocess_r_dataframe(obj)

            # Handle dictionary (e.g. NamedList converted)
            elif isinstance(obj, dict):
                return {k: _recursive_postprocess(v) for k, v in obj.items()}

            # Handle list of items
            elif isinstance(obj, list):
                return [_recursive_postprocess(item) for item in obj]

            return obj  # Primitive values stay as-is

        try:
            r_func = robjects.globalenv[function_name]

            with localconverter(robjects.default_converter + pandas2ri.converter):
                r_args = [robjects.conversion.py2rpy(arg) for arg in args]
                r_kwargs = {k: robjects.conversion.py2rpy(v) for k, v in kwargs.items()}
                result = r_func(*r_args, **r_kwargs)

            # Step 1: Try direct conversion
            with localconverter(robjects.default_converter + pandas2ri.converter):
                py_result = robjects.conversion.rpy2py(result)

            # Step 2: If it's still an R container, convert it
            if isinstance(py_result, (NamedList, ListVector)):
                py_result = r_namedlist_to_dict(py_result)

            # Step 3: Recursively process any nested frames
            return replace_r_na(_recursive_postprocess(py_result))

        except KeyError:
            raise ValueError(f"Function '{function_name}' not found in the R script.")
        except Exception as e:
            raise RuntimeError(f"Error calling R function '{function_name}': {e}")

    @classmethod
    def from_github(
        cls,
        repo: str,
        file_path: str,
        ref: str = "main",
        token: Optional[str] = None,
        cache_dir: Optional[Path] = None,
        path_to_renv: Optional[Path] = None,
        trust_remote_code: bool = False,
        require_token: bool = False,
    ) -> "RFunctionCaller | Path":
        """
        Download an R script from a GitHub repository and construct an RFunctionCaller.

        Args:
            repo: repository in the form "owner/repo".
            file_path: path to the R script inside the repo (e.g. "scripts/my.R").
            ref: branch name, tag or commit SHA. Defaults to "main".
            token: optional GitHub token for private repos. If None, looks at
                environment variables `GITHUB_TOKEN` or `GH_TOKEN`.
            cache_dir: optional directory to cache downloaded files. Defaults to
                `~/.cache/rpy-bridge`.
            path_to_renv: optional path to renv or project directory to use.
            trust_remote_code: MUST be True to execute remote code. If False,
                the function will only return the local cached path.

        Returns:
            If `trust_remote_code` is True, returns an `RFunctionCaller` instance
            ready to call functions from the downloaded script. Otherwise returns
            the `Path` to the cached script so the caller can inspect it first.
        """
        raise NotImplementedError(
            "RFunctionCaller.from_github was removed. Clone repositories locally and pass a local script_path to RFunctionCaller instead."
        )


# %%
def r_namedlist_to_dict(namedlist: object) -> object:
    """
    Recursively convert an R NamedList or ListVector to a Python dictionary.
    - Unwrap atomic R vectors (StrVector, IntVector, etc.) into Python lists or dicts if named.
    - Convert data.frames to pandas DataFrames.
    - Handles NULL or unnamed cases gracefully.
    """

    # -------------------------------------------
    # Handle named lists (NamedList or ListVector)
    # -------------------------------------------
    if isinstance(namedlist, (NamedList, ListVector)):
        names = namedlist.names if not callable(namedlist.names) else namedlist.names()
        result = {}

        # Only iterate if names is not NULL
        if not isinstance(names, NULLType):
            for key, value in zip(names, namedlist):
                key_str = str(key) if key is not None and not isinstance(key, NULLType) else None
                if key_str:
                    result[key_str] = r_namedlist_to_dict(value)
            return result

        # If no names, fallback to a list
        return [r_namedlist_to_dict(value) for value in namedlist]

    # -------------------------------------------
    # Handle atomic vectors (StrVector, IntVector, etc.)
    # These may have names (e.g., c(a = 1, b = 2)) — if so, return a dict.
    # Otherwise, convert to plain Python list.
    # -------------------------------------------
    if isinstance(namedlist, (StrVector, IntVector, FloatVector, BoolVector)):
        names = namedlist.names if not callable(namedlist.names) else namedlist.names()
        if not isinstance(names, NULLType):
            return {
                str(n): v
                for n, v in zip(names, list(namedlist))
                if n is not None and not isinstance(n, NULLType)
            }
        return list(namedlist)

    # -------------------------------------------
    # Attempt conversion via pandas2ri — works for data.frames, tibbles, etc.
    # If it fails, fall back to returning the original R object.
    # -------------------------------------------
    with localconverter(robjects.default_converter + pandas2ri.converter):
        try:
            return robjects.conversion.rpy2py(namedlist)
        except Exception:
            return namedlist


# %%
def clean_r_dataframe(r_df: object) -> object:
    """
    Clean an R data.frame object by removing common non-structural attributes
    like .groups and .rows.
    """
    for attr in [".groups", ".rows"]:
        try:
            del r_df.attr[attr]
        except (KeyError, AttributeError):
            pass
    return r_df


# %%
def fix_string_nans(df: pd.DataFrame) -> pd.DataFrame:
    # Replace common string versions of NA/NaN with actual pd.NA
    return df.replace(["nan", "NaN", "NA", "na", ""], pd.NA)


# %%
def replace_r_na(obj: object) -> object:
    """
    Recursively replace R NA_Character with np.nan in any structure.
    """
    # Handle DataFrame
    if isinstance(obj, pd.DataFrame):
        return (
            obj.replace({ro.NA_Character: np.nan}, regex=False)
            if hasattr(ro, "NA_Character")
            else obj
        )
    elif isinstance(obj, dict):
        return {k: replace_r_na(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [replace_r_na(item) for item in obj]
    elif hasattr(ro, "NA_Character") and obj is ro.NA_Character:
        return np.nan
    else:
        return obj


# %%
def normalize_single_df_dtypes(df: pd.DataFrame) -> pd.DataFrame:
    df = df.replace(["", "nan", "NaN", "NA", "na"], pd.NA)

    for col in df.columns:
        series = df[col]

        # Try converting object/string columns to numeric if possible
        if pd.api.types.is_object_dtype(series):
            coerced = pd.to_numeric(series, errors="coerce")
            # Replace column if conversion produced fewer NaNs (meaning more numeric)
            if coerced.notna().sum() >= series.notna().sum() * 0.5:
                df[col] = coerced

        # Cast integer columns with NA to float to accommodate pd.NA
        if pd.api.types.is_integer_dtype(df[col]):
            if df[col].isna().any():
                df[col] = df[col].astype("float64")

    return df


# %%
def fix_r_dataframe_types(df: pd.DataFrame) -> pd.DataFrame:
    """
    Post-process a DataFrame converted from R via rpy2:
    - Converts numeric columns that represent R dates into datetime
    - Converts timezone-aware datetimes to naive datetimes
    - Replaces R's NA_integer_ sentinel (-2147483648) with pd.NA
    """
    for col in df.columns:
        series = df[col]

        # Fix R's NA_integer_ sentinel (-2147483648)
        if pd.api.types.is_integer_dtype(series):
            if (series == -2147483648).any():
                df[col] = series.mask(series == -2147483648, pd.NA)

        # Convert R-style date columns (days since 1970) to datetime
        if pd.api.types.is_numeric_dtype(series):
            values = series.dropna()
            if not values.empty and values.between(10000, 40000).all():
                try:
                    # "1970-01-01" is the reference date for Unix Epoch
                    df[col] = pd.to_datetime("1970-01-01") + pd.to_timedelta(series, unit="D")
                except Exception:
                    pass

        # Remove timezone from datetime columns (e.g., POSIXct with tz)
        if pd.api.types.is_datetime64tz_dtype(series):
            df[col] = series.dt.tz_localize(None)

    return df


# %%
def postprocess_r_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    df = fix_r_dataframe_types(df)
    df = fix_string_nans(df)
    df = normalize_single_df_dtypes(df)

    # Normalize R-style string index starting from "1"
    if df.index.dtype == object:
        try:
            int_index = df.index.astype(int)
            if (int_index == (np.arange(len(df)) + 1)).all():
                df.index = pd.RangeIndex(start=0, stop=len(df))
        except Exception:
            pass  # leave index as-is if not convertible
    return df


# Note: GitHub fetch helpers were removed to keep the API focused on
# local script invocation. If you need to run remote scripts, clone the
# repository locally and pass the local `script_path` to `RFunctionCaller`.


# %%
# -------------------------------------------
# Functions here onwards are utility functions
# for comparing R and Python DataFrames.
# -------------------------------------------


def normalize_dtypes(df1: pd.DataFrame, df2: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
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
        if (pd.api.types.is_numeric_dtype(dtype1) and pd.api.types.is_object_dtype(dtype2)) or (
            pd.api.types.is_object_dtype(dtype1) and pd.api.types.is_numeric_dtype(dtype2)
        ):
            try:
                df1[col] = pd.to_numeric(s1, errors="coerce")
                df2[col] = pd.to_numeric(s2, errors="coerce")
                continue  # skip to next column if coercion succeeds
            except Exception:
                pass  # fallback to next block if coercion fails

        # If both are numeric but of different types (e.g., int vs float), unify to float64
        if pd.api.types.is_numeric_dtype(dtype1) and pd.api.types.is_numeric_dtype(dtype2):
            df1[col] = df1[col].astype("float64")
            df2[col] = df2[col].astype("float64")
            continue

        # If both are objects or strings, convert both to str for equality comparison
        if pd.api.types.is_object_dtype(dtype1) or pd.api.types.is_object_dtype(dtype2):
            df1[col] = df1[col].astype(str)
            df2[col] = df2[col].astype(str)

    return df1, df2


# %%
def align_numeric_dtypes(df1: pd.DataFrame, df2: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
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
def compare_r_py_dataframes(df1: pd.DataFrame, df2: pd.DataFrame, float_tol: float = 1e-8) -> dict:
    """
    Compare a Python DataFrame (df1) with an R DataFrame converted to pandas (df2).

    Returns:
        dict with mismatch diagnostics, preserving original indices in diffs.
    """

    results = {
        "shape_mismatch": False,
        "columns_mismatch": False,
        "index_mismatch": False,
        "numeric_diffs": {},
        "non_numeric_diffs": {},
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

        if pd.api.types.is_numeric_dtype(col_py) and pd.api.types.is_numeric_dtype(col_r):
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
