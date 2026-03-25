# src/core/logging.py
# Structured JSON logging for NeuroOps Agent Platform.

import json
import logging
import sys
from datetime import datetime, timezone

# Fields that are built into every LogRecord — excluded from the JSON extras
_BUILTIN_FIELDS = {
    "name", "msg", "args", "levelname", "levelno", "pathname", "filename",
    "module", "exc_info", "exc_text", "stack_info", "lineno", "funcName",
    "created", "msecs", "relativeCreated", "thread", "threadName",
    "processName", "process", "message", "taskName",
}


class JsonFormatter(logging.Formatter):
    """Formats every log record as a single-line JSON object.

    Any key passed via ``extra={}`` is merged into the JSON output,
    making it easy to attach structured fields (request_id, latency, etc.)
    without polluting the message string.
    """

    def format(self, record: logging.LogRecord) -> str:
        log_obj: dict = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        }
        if record.exc_info:
            log_obj["exc"] = self.formatException(record.exc_info)
        # Merge any extra fields passed by the caller
        for key, val in record.__dict__.items():
            if key not in _BUILTIN_FIELDS:
                log_obj[key] = val
        return json.dumps(log_obj)


def configure_logging(log_level: str = "INFO") -> None:
    """Configure the root logger with JSON output.

    Call once at application startup. Replaces any existing handlers so that
    uvicorn's default formatter does not produce duplicate or mixed output.
    """
    level = getattr(logging, log_level.upper(), logging.INFO)

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())

    root = logging.getLogger()
    root.setLevel(level)
    root.handlers.clear()
    root.addHandler(handler)

    # Suppress uvicorn's own access log — our request_id middleware logs
    # one structured line per request instead.
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Return a named logger. Use module __name__ as the name convention."""
    return logging.getLogger(name)
