"""ClAP shared logging for Python services.

Provides consistent logging across all Python ClAP services with:
- Matching format to log_utils.sh: [YYYY-MM-DD HH:MM:SS] [LEVEL] [component] message
- Dual output: stdout (for journald) + rotating file (for grep/tail)
- Flush after every write (belt + suspenders with PYTHONUNBUFFERED)
- 10MB rotation, 5 backup files

Usage:
    from clap_logger import get_logger
    logger = get_logger("autonomous-timer")
    logger.info("Starting up")
    logger.error("Connection failed", exc_info=True)
"""

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path


CLAP_DIR = Path.home() / "claude-autonomy-platform"
LOG_DIR = CLAP_DIR / "logs"
MAX_BYTES = 10 * 1024 * 1024  # 10MB
BACKUP_COUNT = 5
LOG_FORMAT = "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


class FlushingStreamHandler(logging.StreamHandler):
    """StreamHandler that flushes after every emit."""

    def emit(self, record):
        super().emit(record)
        self.flush()


class FlushingRotatingFileHandler(RotatingFileHandler):
    """RotatingFileHandler that flushes after every emit."""

    def emit(self, record):
        super().emit(record)
        self.stream.flush()


def get_logger(
    name: str,
    log_file: str | None = None,
    level: int = logging.INFO,
) -> logging.Logger:
    """Get a configured logger for a ClAP component.

    Args:
        name: Component name (e.g. "autonomous-timer"). Used in log format
              and as default filename ({name}.log).
        log_file: Override log filename. Defaults to {name}.log in logs/.
        level: Logging level. Defaults to INFO.

    Returns:
        Configured logger instance.
    """
    logger = logging.getLogger(f"clap.{name}")

    # Don't add handlers if already configured
    if logger.handlers:
        return logger

    logger.setLevel(level)
    formatter = logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)

    # Stdout handler (captured by journald when running as systemd service)
    stdout_handler = FlushingStreamHandler(sys.stdout)
    stdout_handler.setFormatter(formatter)
    logger.addHandler(stdout_handler)

    # Rotating file handler
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    if log_file is None:
        log_file = f"{name}.log"
    file_path = LOG_DIR / log_file
    file_handler = FlushingRotatingFileHandler(
        file_path,
        maxBytes=MAX_BYTES,
        backupCount=BACKUP_COUNT,
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Prevent propagation to root logger (avoids duplicate output)
    logger.propagate = False

    return logger
