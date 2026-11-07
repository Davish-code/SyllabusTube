"""Logging configuration with secret redaction and rotating file support."""

from __future__ import annotations

import logging
import re
from logging.handlers import RotatingFileHandler
from pathlib import Path

# Regular expressions detecting common API key patterns:
# - Google/Gemini/YouTube API keys typically start with AIzaSy and are ~39 chars
# - Generic hex/base64-like keys of length >= 20 following keywords
API_KEY_PATTERNS = [
    re.compile(r"AIza[0-9A-Za-z-_]{35}"),
    re.compile(
        r"(api[_-]?key|secret|token|auth)['\":=\s]+(['\"]?)([A-Za-z0-9-_]{16,})(['\"]?)",
        re.IGNORECASE,
    ),
    re.compile(r"Bearer\s+([A-Za-z0-9-_\.]+)", re.IGNORECASE),
]


class RedactingFormatter(logging.Formatter):
    """Custom logging formatter that redacts detected API keys and secrets."""

    def format(self, record: logging.LogRecord) -> str:
        original = super().format(record)
        return self.redact(original)

    @staticmethod
    def redact(text: str) -> str:
        """Redact known sensitive patterns from the text."""
        # 1. Redact Google API key specifically (AIza...)
        text = re.sub(r"AIza[0-9A-Za-z-_]{35}", "[REDACTED_API_KEY]", text)

        # 2. Redact key=value or secret assignments
        def _mask_assignment(match: re.Match[str]) -> str:
            prefix = match.group(1)
            q1 = match.group(2) or ""
            secret = match.group(3)
            q2 = match.group(4) or ""
            masked = secret[:3] + "..." + secret[-3:] if len(secret) > 8 else "***"
            return f"{prefix}{q1}{masked}{q2}"

        text = API_KEY_PATTERNS[1].sub(_mask_assignment, text)

        # 3. Redact Bearer tokens
        text = re.sub(
            r"(Bearer\s+)[A-Za-z0-9-_\.]{8,}", r"\1[REDACTED_TOKEN]", text, flags=re.IGNORECASE
        )
        return text


def setup_logging(
    log_file: str | Path | None = "cache/syllabustube.log",
    verbose: bool = False,
    max_bytes: int = 5 * 1024 * 1024,
    backup_count: int = 3,
) -> logging.Logger:
    """Configure root and package logger with console and rotating file output.

    Args:
        log_file: Path to rotating log file. If None or directory unwritable, skips file logging.
        verbose: If True, set level to DEBUG; else INFO.
        max_bytes: Max size before log rotates.
        backup_count: Number of rotated files to retain.

    Returns:
        Configured logger instance for 'syllabustube'.
    """
    logger = logging.getLogger("syllabustube")
    level = logging.DEBUG if verbose else logging.INFO
    logger.setLevel(level)

    # Avoid duplicate handlers if setup_logging is called multiple times
    if logger.handlers:
        logger.handlers.clear()

    formatter = RedactingFormatter(
        fmt="%(asctime)s [%(levelname)s] %(name)s (%(filename)s:%(lineno)d): %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Console Handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # Rotating File Handler
    if log_file:
        try:
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            file_handler = RotatingFileHandler(
                log_path,
                maxBytes=max_bytes,
                backupCount=backup_count,
                encoding="utf-8",
            )
            file_handler.setLevel(logging.DEBUG)  # Always log DEBUG to file
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        except OSError:
            # Fall back gracefully if unable to write log file
            pass

    return logger


def get_logger(name: str = "syllabustube") -> logging.Logger:
    """Get a child or root logger for the package."""
    return logging.getLogger(name)
