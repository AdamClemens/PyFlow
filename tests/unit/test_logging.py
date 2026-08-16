"""Unit tests for pyflow.engine.logging_setup (TASK-006)."""

import logging

from pyflow.configuration import LoggingConfig
from pyflow.engine import configure_logging, get_logger


def test_configure_logging_sets_level() -> None:
    configure_logging(LoggingConfig(level="DEBUG"))
    assert logging.getLogger("pyflow").level == logging.DEBUG

    configure_logging(LoggingConfig(level="WARNING"))
    assert logging.getLogger("pyflow").level == logging.WARNING


def test_configure_logging_does_not_accumulate_handlers() -> None:
    configure_logging(LoggingConfig())
    configure_logging(LoggingConfig())
    configure_logging(LoggingConfig())

    assert len(logging.getLogger("pyflow").handlers) == 1


def test_child_loggers_inherit_configured_level() -> None:
    configure_logging(LoggingConfig(level="ERROR"))

    child = get_logger("pyflow.engine.some_module")

    assert child.getEffectiveLevel() == logging.ERROR


def test_get_logger_returns_stdlib_logger() -> None:
    logger = get_logger(__name__)
    assert isinstance(logger, logging.Logger)
    assert logger.name == __name__
