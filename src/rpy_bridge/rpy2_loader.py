"""
Lazy loader for rpy2 objects and converters.

Provides cached access to rpy2 modules to avoid repeated imports.
"""

from __future__ import annotations

from typing import Any

_RPY2: dict[str, Any] | None = None


def _require_rpy2(raise_on_missing: bool = True) -> dict[str, Any] | None:
    """
    Import rpy2 lazily and cache its key objects.
    """
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

    except ImportError as exc:
        if raise_on_missing:
            raise RuntimeError(
                "R support requires rpy2; install it in your Python env (e.g., pip install rpy2)"
            ) from exc
        return None


def ensure_rpy2() -> dict[str, Any]:
    """
    Return the cached rpy2 bundle, raising if unavailable.
    """
    global _RPY2
    if _RPY2 is None:
        _RPY2 = _require_rpy2()
    assert _RPY2 is not None, "_require_rpy2() returned None"
    return _RPY2


__all__ = ["ensure_rpy2", "_require_rpy2"]
