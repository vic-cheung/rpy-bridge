"""
Conversion helpers for R ↔ Python interop.

These utilities are used by RFunctionCaller and exposed for compatibility.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
import pandas as pd

from .rpy2_loader import ensure_rpy2

if TYPE_CHECKING:  # pragma: no cover - typing only
    from .core import RFunctionCaller


def r_namedlist_to_dict(namedlist, caller: "RFunctionCaller", top_level: bool = False):
    r = ensure_rpy2()
    NamedList = r["NamedList"]
    ListVector = r["ListVector"]

    if isinstance(namedlist, (NamedList, ListVector)):
        names = namedlist.names if not callable(namedlist.names) else namedlist.names()

        if names and all(str(i) == str(name) for i, name in enumerate(names)):
            out = []
            for val in namedlist:
                out.append(caller._r2py(val, top_level=False))
            return out

        result = {}
        for i, val in enumerate(namedlist):
            key = names[i] if names and i < len(names) else str(i)
            result[str(key)] = caller._r2py(val, top_level=False)
        return result

    return caller._r2py(namedlist, top_level=top_level)


def clean_r_missing(obj, caller: "RFunctionCaller"):
    robjects = caller.robjects
    na_map = {
        getattr(robjects, "NA_Real", None): np.nan,
        getattr(robjects, "NA_Integer", None): np.nan,
        getattr(robjects, "NA_Logical", None): np.nan,
        getattr(robjects, "NA_Character", None): pd.NA,
    }

    if isinstance(obj, pd.DataFrame):
        for col in obj.columns:
            obj[col] = obj[col].apply(lambda x: clean_r_missing(x, caller))
        return obj
    if isinstance(obj, dict):
        return {k: clean_r_missing(v, caller) for k, v in obj.items()}
    if isinstance(obj, list):
        return [clean_r_missing(v, caller) for v in obj]
    return na_map.get(obj, obj)


__all__ = ["r_namedlist_to_dict", "clean_r_missing"]
