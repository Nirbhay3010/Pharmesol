import logging

import structlog


def setup_logging(level: int = logging.INFO):
    """Configure structlog with JSON output for production."""
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.dev.ConsoleRenderer()
            if _is_dev()
            else structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(level),
    )


def _is_dev() -> bool:
    """Use human-readable logs in development."""
    import os
    return os.getenv("ENVIRONMENT", "development") == "development"
