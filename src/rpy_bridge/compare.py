"""
DataFrame comparison helpers used to validate parity between R and Python outputs.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from .dataframe import fix_r_dataframe_types, fix_string_nans


def normalize_dtypes(df1: pd.DataFrame, df2: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    for col in df1.columns.intersection(df2.columns):
        df1[col] = df1[col].replace("", pd.NA)
        df2[col] = df2[col].replace("", pd.NA)
        s1, s2 = df1[col], df2[col]
        dtype1, dtype2 = s1.dtype, s2.dtype
        if (pd.api.types.is_numeric_dtype(dtype1) and pd.api.types.is_object_dtype(dtype2)) or (
            pd.api.types.is_object_dtype(dtype1) and pd.api.types.is_numeric_dtype(dtype2)
        ):
            try:
                df1[col] = pd.to_numeric(s1, errors="coerce")
                df2[col] = pd.to_numeric(s2, errors="coerce")
                continue
            except Exception:
                pass
        if pd.api.types.is_numeric_dtype(dtype1) and pd.api.types.is_numeric_dtype(dtype2):
            df1[col] = df1[col].astype("float64")
            df2[col] = df2[col].astype("float64")
            continue
        if pd.api.types.is_object_dtype(dtype1) or pd.api.types.is_object_dtype(dtype2):
            df1[col] = df1[col].astype(str)
            df2[col] = df2[col].astype(str)
    return df1, df2


def align_numeric_dtypes(df1: pd.DataFrame, df2: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    for col in df1.columns.intersection(df2.columns):
        s1, s2 = df1[col].replace("", pd.NA), df2[col].replace("", pd.NA)
        try:
            s1_num = pd.to_numeric(s1, errors="coerce")
            s2_num = pd.to_numeric(s2, errors="coerce")
            if not s1_num.isna().all() or not s2_num.isna().all():
                df1[col] = s1_num.astype("float64")
                df2[col] = s2_num.astype("float64")
                continue
        except Exception:
            pass
        df1[col], df2[col] = s1, s2
    return df1, df2


def compare_r_py_dataframes(df1: pd.DataFrame, df2: pd.DataFrame, float_tol: float = 1e-8) -> dict:
    results: dict[str, Any] = {
        "shape_mismatch": False,
        "columns_mismatch": False,
        "index_mismatch": False,
        "numeric_diffs": {},
        "non_numeric_diffs": {},
    }
    df2 = fix_r_dataframe_types(df2)
    df1 = fix_string_nans(df1)
    df2 = fix_string_nans(df2)
    df1, df2 = normalize_dtypes(df1.copy(), df2.copy())
    df1, df2 = align_numeric_dtypes(df1, df2)
    if df1.shape != df2.shape:
        results["shape_mismatch"] = True
        print(f"[Warning] Shape mismatch: df1 {df1.shape} vs df2 {df2.shape}")
    if set(df1.columns) != set(df2.columns):
        results["columns_mismatch"] = True
        print("[Warning] Column mismatch:")
        print(f"  df1: {df1.columns}")
        print(f"  df2: {df2.columns}")
        common_cols = df1.columns.intersection(df2.columns)
    else:
        common_cols = df1.columns
    df1_aligned, df2_aligned = df1.loc[:, common_cols], df2.loc[:, common_cols]
    for col in common_cols:
        col_py, col_r = df1_aligned[col], df2_aligned[col]
        if pd.api.types.is_numeric_dtype(col_py) and pd.api.types.is_numeric_dtype(col_r):
            col_py, col_r = col_py.align(col_r)
            close = np.isclose(
                col_py.fillna(np.nan),
                col_r.fillna(np.nan),
                atol=float_tol,
                equal_nan=True,
            )
            if not close.all():
                results["numeric_diffs"][col] = pd.DataFrame(
                    {"df1": col_py[~close], "df2": col_r[~close]}
                )
        else:
            unequal = ~col_py.eq(col_r)
            both_na = col_py.isna() & col_r.isna()
            unequal = unequal & ~both_na
            if unequal.any():
                results["non_numeric_diffs"][col] = pd.DataFrame(
                    {"df1": col_py[unequal], "df2": col_r[unequal]}
                )
    return results


__all__ = ["normalize_dtypes", "align_numeric_dtypes", "compare_r_py_dataframes"]
