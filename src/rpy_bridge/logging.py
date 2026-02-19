"""
Logging utilities for rpy-bridge.

Sets up a stdlib `logging` logger and a dedicated
`[RFunctionCaller]` handler used throughout the package.
"""

from __future__ import annotations

import logging
import sys
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover - typing only
    LoggerType = logging.Logger
else:
    LoggerType = None


# Configure package logger
logging.basicConfig()
logger = logging.getLogger("rpy-bridge")
logger.setLevel(logging.INFO)


# Ensure handler writes to stderr and uses a compact formatter. A filter
# injects a `tag` attribute (used for the RFunctionCaller handler) so the
# formatter remains robust for records without a tag.
class _TagFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:  # pragma: no cover - simple passthrough
        if not hasattr(record, "tag"):
            record.tag = ""
        return True


handler = logging.StreamHandler(sys.stderr)
formatter = logging.Formatter(
    "%(asctime)s | %(levelname)s | %(tag)s %(message)s", "%Y-%m-%d %H:%M:%S"
)
handler.setFormatter(formatter)
handler.addFilter(_TagFilter())

# Avoid adding duplicate handlers when this module is imported multiple times
if not any(isinstance(h, logging.StreamHandler) for h in logger.handlers):
    logger.addHandler(handler)


# Dedicated logger adapter for R function call tracing
_rfc_logger = logging.LoggerAdapter(logger, {"tag": "[RFunctionCaller]"})


def log_r_call(func_name: str, source_info: str) -> None:
    """
    Log an R function call with minimal noise.
    """
    # Keep call site depth minimal: use INFO level and a concise message.
    _rfc_logger.info(
        "[rpy-bridge.RFunctionCaller] Called R function '%s' from %s", func_name, source_info
    )


__all__ = ["logger", "_rfc_logger", "log_r_call", "LoggerType"]
