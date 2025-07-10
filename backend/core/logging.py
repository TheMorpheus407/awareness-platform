"""Logging configuration using loguru."""

import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict

from loguru import logger

from core.config import settings


class InterceptHandler(logging.Handler):
    """Intercept standard logging messages and redirect to loguru."""
    
    def emit(self, record: logging.LogRecord) -> None:
        """Emit a log record to loguru."""
        # Get corresponding Loguru level if it exists
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno
        
        # Find caller from where originated the logged message
        frame, depth = logging.currentframe(), 2
        while frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1
        
        logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )


def serialize_record(record: Dict[str, Any]) -> str:
    """Serialize log record to JSON format."""
    # Handle timestamp safely
    timestamp = None
    if "time" in record and hasattr(record["time"], "timestamp"):
        timestamp = record["time"].timestamp()
    elif "time" in record:
        timestamp = str(record["time"])
    
    subset = {
        "timestamp": timestamp,
        "message": record.get("message", ""),
        "level": record.get("level", {}).get("name", "INFO") if isinstance(record.get("level"), dict) else str(record.get("level", "INFO")),
        "module": record.get("module", ""),
        "function": record.get("function", ""),
        "line": record.get("line", 0),
    }
    
    # Add extra fields
    if record.get("extra"):
        subset.update(record["extra"])
    
    # Add exception info if present
    if record.get("exception"):
        subset["exception"] = str(record["exception"])
    
    return json.dumps(subset)


def setup_logging() -> None:
    """Configure logging for the application."""
    # Remove default logger
    logger.remove()
    
    # Skip complex logging setup in test environment
    if settings.ENVIRONMENT == "test" or settings.TESTING:
        # Simple console output for tests
        logger.add(
            sys.stderr,
            format="{time} | {level} | {message}",
            level="INFO",
            colorize=False,
        )
        return
    
    # Console logging with colors
    if settings.is_development:
        logger.add(
            sys.stderr,
            format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
                   "<level>{level: <8}</level> | "
                   "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
                   "<level>{message}</level>",
            level=settings.LOG_LEVEL,
            colorize=True,
            backtrace=True,
            diagnose=True,
        )
    else:
        # Production: JSON logs without colors
        logger.add(
            sys.stdout,
            format=serialize_record,
            level=settings.LOG_LEVEL,
            colorize=False,
            serialize=True,
            backtrace=False,
            diagnose=False,
        )
    
    # File logging
    if settings.is_production:
        log_dir = Path("/var/log/cybersecurity-platform")
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # General application logs
        logger.add(
            log_dir / "app.log",
            rotation="500 MB",
            retention="30 days",
            compression="zip",
            level="INFO",
            format=serialize_record,
            serialize=True,
            backtrace=False,
            diagnose=False,
        )
        
        # Error logs
        logger.add(
            log_dir / "error.log",
            rotation="100 MB",
            retention="60 days",
            compression="zip",
            level="ERROR",
            format=serialize_record,
            serialize=True,
            backtrace=True,
            diagnose=True,
        )
        
        # Access logs
        logger.add(
            log_dir / "access.log",
            rotation="1 day",
            retention="7 days",
            compression="zip",
            level="INFO",
            filter=lambda record: "access" in record["extra"],
            format=serialize_record,
            serialize=True,
        )
    
    # Intercept standard logging
    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)
    
    # Intercept uvicorn logs
    for logger_name in ["uvicorn", "uvicorn.error", "uvicorn.access"]:
        logging_logger = logging.getLogger(logger_name)
        logging_logger.handlers = [InterceptHandler()]
        logging_logger.propagate = False
    
    # Intercept sqlalchemy logs
    for logger_name in ["sqlalchemy.engine", "sqlalchemy.pool"]:
        logging_logger = logging.getLogger(logger_name)
        logging_logger.handlers = [InterceptHandler()]
        logging_logger.propagate = False
        # Set appropriate level for SQL logs
        if settings.is_development and settings.LOG_LEVEL == "DEBUG":
            logging_logger.setLevel(logging.DEBUG)
        else:
            logging_logger.setLevel(logging.WARNING)
    
    logger.info(f"Logging configured with level: {settings.LOG_LEVEL}")


# Export logger instance
__all__ = ["logger", "setup_logging"]