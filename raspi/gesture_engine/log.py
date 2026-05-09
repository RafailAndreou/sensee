"""Centralized logging setup for the Sensee runtime.

Use ``get_logger(__name__)`` in each module instead of ``print``. Logging is
configured once on first import via :func:`configure_logging`; subsequent
calls are no-ops, so it's safe to call from multiple entry points.
"""

from __future__ import annotations

import logging
import os
import sys

_DEFAULT_LEVEL = os.environ.get("SENSEE_LOG_LEVEL", "INFO").upper()
_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
_DATEFMT = "%H:%M:%S"
_configured = False


def configure_logging(level: str | int | None = None) -> None:
    """Install a single stderr handler on the root logger."""
    global _configured
    if _configured:
        return

    root = logging.getLogger()
    root.setLevel(level or _DEFAULT_LEVEL)

    handler = logging.StreamHandler(stream=sys.stderr)
    handler.setFormatter(logging.Formatter(_FORMAT, datefmt=_DATEFMT))
    root.addHandler(handler)

    _configured = True


def get_logger(name: str) -> logging.Logger:
    """Return a module-scoped logger; ensures global config is loaded."""
    configure_logging()
    return logging.getLogger(name)
