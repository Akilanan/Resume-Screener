import logging
import sys
import json
from datetime import datetime


class JSONFormatter(logging.Formatter):
    """Custom JSON log formatter for structured logging to stdout → Loki/Grafana."""

    def format(self, record):
        return json.dumps({
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "service": "backend",
            "message": record.getMessage(),
            "module": record.module,
            "func": record.funcName,
        })


def setup_logging():
    """Initialize structured JSON logging."""
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONFormatter())
    logging.basicConfig(level=logging.INFO, handlers=[handler])
