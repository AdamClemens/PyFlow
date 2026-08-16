"""Centralised logging configuration (TASK-006).

Every pyflow subsystem gets its logger through `get_logger`, and a run
configures logging once through `configure_logging` -- one place decides
level and formatting, rather than each module reaching for
`logging.basicConfig` (or worse, print) independently.

Configures the `pyflow` logger, not the real root logger -- that keeps
this from also reconfiguring torch's, pygfx's, or any other dependency's
logging just because pyflow started up. Every pyflow module's logger
(`logging.getLogger(__name__)`, e.g. `pyflow.engine.mesh`) is a child of
`pyflow` and inherits its level and handler through the normal logging
hierarchy -- "every subsystem logs through the common framework" falls
out of that convention, not from a bespoke mechanism.
"""

from __future__ import annotations

import logging

from pyflow.configuration.schema import LoggingConfig

_PACKAGE_LOGGER_NAME = "pyflow"


def configure_logging(config: LoggingConfig) -> None:
    """Configure the `pyflow` logger hierarchy. Call once, at startup.

    Safe to call more than once (e.g. across tests): replaces the
    handler rather than accumulating a duplicate on each call.
    """
    logger = logging.getLogger(_PACKAGE_LOGGER_NAME)
    logger.setLevel(config.level.upper())
    logger.propagate = False

    logger.handlers.clear()
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)-8s %(name)s: %(message)s"))
    logger.addHandler(handler)


def get_logger(name: str) -> logging.Logger:
    """Return the logger for `name` (conventionally a module's `__name__`).

    A thin wrapper around `logging.getLogger`, kept as the one documented
    entry point subsystems use, so the `pyflow`-hierarchy convention above
    is documented in one place instead of assumed at every call site.
    """
    return logging.getLogger(name)
