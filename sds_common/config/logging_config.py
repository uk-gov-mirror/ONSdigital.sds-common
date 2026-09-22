import json
import logging
import os
import traceback as _traceback


def get_log_level() -> int:
    """
    Get the logging level from the LOG_LEVEL environment variable, or use the default value of INFO.

    :return int: logging level
    """
    log_level = os.environ.get("LOG_LEVEL", "INFO")
    return getattr(logging, log_level)


class GcpJsonFormatter(logging.Formatter):
    """
    Formats log records as single-line JSON objects compatible with Google Cloud Logging.

    GCP parses the ``severity`` field to set the log level in Cloud Logging,
    enabling correct colouring, filtering, and alerting in the console.

    Behaviour:
    - ``traceback``: included when an exception is active (e.g. inside ``except`` or via
      ``logger.exception()``).
    - ``stackTrace``: automatically captured for ``WARNING`` level and above, so you always
      know where in the call stack a warning or error originated. Also included when
      ``stack_info=True`` is passed explicitly on lower-severity records.
    """

    def format(self, record: logging.LogRecord) -> str:
        entry: dict = {
            "severity": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
        }
        if record.exc_info:
            entry["traceback"] = self.formatException(record.exc_info)
        if record.stack_info:
            entry["stackTrace"] = self.formatStack(record.stack_info)
        elif record.levelno >= logging.WARNING:
            entry["stackTrace"] = "".join(_traceback.format_stack())
        return json.dumps(entry)


def configure_gcp_logging(level: int | None = None) -> None:
    """
    Configure the root logger to emit JSON-structured logs for Google Cloud Logging.

    This is called automatically on import if no logging handlers are already configured,
    so most applications will not need to call this explicitly. Call it directly only if
    you need to override the log level or re-configure logging after another library has
    already set up handlers.

    :param level: Optional log level (e.g. ``logging.DEBUG``). Defaults to the value
                  of the ``LOG_LEVEL`` environment variable, or ``INFO`` if not set.

    Example::

        from sds_common import configure_gcp_logging
        configure_gcp_logging(level=logging.DEBUG)
    """
    handler = logging.StreamHandler()
    handler.setFormatter(GcpJsonFormatter())
    logging.basicConfig(
        handlers=[handler],
        level=level if level is not None else get_log_level(),
        force=True,
    )


# Auto-configure GCP structured logging on import if the root logger is unconfigured.
# This is safe — logging.basicConfig is a no-op if handlers are already present,
# but we check explicitly so force=True is only used when the user calls this directly.
if not logging.root.handlers:
    configure_gcp_logging()
