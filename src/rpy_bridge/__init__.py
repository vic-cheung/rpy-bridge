"""
Public API for the rpy-bridge package.

This module re-exports the helpers that wrap rpy2 so downstream users can
continue importing directly from ``rpy_bridge``.
"""

from .rpy2_utils import (
    NamespaceWrapper,
    RFunctionCaller,
    activate_renv,
    align_numeric_dtypes,
    clean_r_dataframe,
    clean_r_missing,
    compare_r_py_dataframes,
    fix_r_dataframe_types,
    fix_string_nans,
    normalize_dtypes,
    normalize_single_df_dtypes,
    postprocess_r_dataframe,
    r_namedlist_to_dict,
)

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
]
