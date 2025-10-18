"""Logging utilities for Project Empathy."""

from __future__ import annotations

import logging
from logging import Logger
from typing import Optional


LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"


def configure_logging(level: int = logging.INFO, name: str = "project_empathy") -> Logger:
    """Configure and return a logger.

    Parameters
    ----------
    level:
        Logging level for the root handler.
    name:
        Name of the logger to configure.
    """

    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(LOG_FORMAT)
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    logger.setLevel(level)
    return logger


def get_logger(name: Optional[str] = None) -> Logger:
    """Return a configured logger for the given module name."""

    root_name = "project_empathy"
    full_name = root_name if name is None else f"{root_name}.{name}"
    return configure_logging(name=full_name)
