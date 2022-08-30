import logging
import logging.config
import sys

from typing import Dict, Any


DEFAULT_LOGGING_CONFIG: Dict[str, Any] = {
    "version": 1,
    "formatters": {
        "verbose_formatter": {
            "format": "(%(process)d) %(asctime)s %(name)s (line %(lineno)s) | %(levelname)s %(message)s"
        },
        "normal_formatter": {"format": "%(levelname)s %(message)s"},
    },
    "handlers": {
        "console_stdout": {
            # Sends log messages that are higher than INFO level with minimal format
            "class": "logging.StreamHandler",
            "level": "INFO",
            "formatter": "normal_formatter",
            "stream": sys.stdout,
        },
        "console_stdout_verbose": {
            # Sends all log messages that are higher than DEBUG with verbose format
            # Useful for debugging purposes
            "class": "logging.StreamHandler",
            "level": "DEBUG",
            "formatter": "verbose_formatter",
            "stream": sys.stdout,
        },
    },
    "root": {
        # In general, this should be kept at 'NOTSET'.
        # Otherwise it would interfere with the log levels set for each handler.
        "level": "NOTSET",
        "handlers": ["console_stdout"],
    },
}


def setup_logging(verbose: bool = False):
    if verbose:
        DEFAULT_LOGGING_CONFIG["root"]["handlers"] = ["console_stdout_verbose"]
    logging.config.dictConfig(DEFAULT_LOGGING_CONFIG)
