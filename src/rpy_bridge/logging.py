"""
Logging utilities for rpy-bridge.

Sets up a loguru-backed logger (fallback to the stdlib logger) and a dedicated
[RFunctionCaller] sink used throughout the package.
"""

from __future__ import annotations

import logging
import sys
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover - typing only
    from loguru import Logger as LoguruLogger

    LoggerType = LoguruLogger | logging.Logger
else:  # pragma: no cover - runtime does not need the alias
    LoggerType = None

try:
    from loguru import logger as loguru_logger  # type: ignore

    logger = loguru_logger
except ImportError:  # pragma: no cover - fallback when loguru is absent
    logging.basicConfig()
    logger = logging.getLogger("rpy-bridge")

# Remove default handler to override global default
logger.remove()

# Add a sink for RFunctionCaller logs
_rfc_logger = logger.bind(tag="[RFunctionCaller]")
_rfc_logger.add(
    sys.stderr,
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
    level="INFO",
)


def log_r_call(func_name: str, source_info: str) -> None:
    """Log an R function call with minimal noise."""
    _rfc_logger.opt(depth=1, record=False).info(
        "[rpy-bridge.RFunctionCaller] Called R function '{}' from {}",
        func_name,
        source_info,
    )


__all__ = ["logger", "_rfc_logger", "log_r_call", "LoggerType"]
