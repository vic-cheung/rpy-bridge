"""
DataFrame cleaning and post-processing utilities for R ↔ Python workflows.
"""

from __future__ import annotations

import re

import numpy as np
import pandas as pd


def clean_r_dataframe(r_df: pd.DataFrame) -> pd.DataFrame:
    for attr in [".groups", ".rows"]:
        try:
            del r_df.attrs[attr]
        except (KeyError, AttributeError):
            pass
    return r_df


def fix_string_nans(df: pd.DataFrame) -> pd.DataFrame:
    return df.replace(["nan", "NaN", "NA", "na", ""], pd.NA)


def normalize_single_df_dtypes(df: pd.DataFrame) -> pd.DataFrame:
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


# Token-based patterns to detect date/time columns; avoids substring matches like "endotoxin" or "runtime".
_DATE_TOKEN_RE = re.compile(
    r"(?<![a-z0-9])"
    r"(?:date|dt|time|dob|visit|start|end|created|updated|modified|timestamp|datetime|ts|dos)"
    r"(?![a-z0-9])",
    re.IGNORECASE,
)


def _looks_like_date_column(col_name: str) -> bool:
    """Check if column name suggests it contains date values."""
    col_lower = str(col_name).lower()
    return bool(_DATE_TOKEN_RE.search(col_lower))


def fix_r_dataframe_types(df: pd.DataFrame) -> pd.DataFrame:
    for col in df.columns:
        series = df[col]
        if pd.api.types.is_integer_dtype(series):
            df[col] = series.mask(series == -2147483648, pd.NA)
        if pd.api.types.is_numeric_dtype(series):
            values = series.dropna()
            # Only convert to date if values are in R's date range AND column name suggests a date
            if (
                not values.empty
                and values.between(10000, 40000).all()
                and _looks_like_date_column(col)
            ):
                try:
                    df[col] = pd.to_datetime("1970-01-01") + pd.to_timedelta(series, unit="D")
                except Exception:
                    pass
        if pd.api.types.is_datetime64tz_dtype(series):
            df[col] = series.dt.tz_convert(None)
    return df


def postprocess_r_dataframe(df: pd.DataFrame) -> pd.DataFrame:
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


__all__ = [
    "clean_r_dataframe",
    "fix_string_nans",
    "normalize_single_df_dtypes",
    "fix_r_dataframe_types",
    "postprocess_r_dataframe",
]
