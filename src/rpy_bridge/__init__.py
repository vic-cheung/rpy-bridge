"""
Public API for the rpy-bridge package.

`RFunctionCaller` is the primary entry point for loading R scripts and calling
functions. Other helpers are re-exported for compatibility.
"""

from .core import RFunctionCaller
from .renv import activate_renv

__all__ = [
    "activate_renv",
    "RFunctionCaller",
]
