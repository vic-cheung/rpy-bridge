"""
Compatibility shim for the legacy rpy2_utils module.

The implementation now lives in smaller modules (core, env, renv, convert,
dataframe, compare), but imports remain available from this namespace to
avoid breaking existing code. `RFunctionCaller` remains the primary interface.
"""

from __future__ import annotations

from .compare import align_numeric_dtypes, compare_r_py_dataframes, normalize_dtypes
from .convert import clean_r_missing, r_namedlist_to_dict
from .core import NamespaceWrapper, RFunctionCaller
from .dataframe import (
    clean_r_dataframe,
    fix_r_dataframe_types,
    fix_string_nans,
    normalize_single_df_dtypes,
    postprocess_r_dataframe,
)
from .env import CI_TESTING, R_HOME, ensure_rpy2_available, find_r_home
from .renv import activate_renv

__all__ = [
    "activate_renv",
    "RFunctionCaller",
    "NamespaceWrapper",
    "r_namedlist_to_dict",
    "clean_r_dataframe",
    "fix_string_nans",
    "clean_r_missing",
    "normalize_single_df_dtypes",
    "fix_r_dataframe_types",
    "postprocess_r_dataframe",
    "normalize_dtypes",
    "align_numeric_dtypes",
    "compare_r_py_dataframes",
    "ensure_rpy2_available",
    "find_r_home",
    "CI_TESTING",
    "R_HOME",
]
