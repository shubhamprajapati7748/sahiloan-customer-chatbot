import os
import sys
import uuid
from contextvars import ContextVar
from enum import Enum
from typing import Optional

from loguru import logger as _loguru_logger

# Re-export logger for easier imports
logger = _loguru_logger

# Context variables for tracking request context across async/threading
request_id_var: ContextVar[Optional[str]] = ContextVar("request_id", default=None)
user_id_var: ContextVar[Optional[str]] = ContextVar("user_id", default=None)


class LogProfile(str, Enum):
    """Environment profiles for logging configuration"""

    LOCAL = "local"
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class LogConfig:
    """Centralized logging configuration"""

    # Profile-specific configurations
    PROFILE_CONFIGS = {
        LogProfile.LOCAL: {
            "console_level": "DEBUG",
            "file_level": "DEBUG",
            "rotation": "50 MB",
            "retention": "3 days",
            "compression": None,
            "serialize": False,
            "backtrace": True,
            "diagnose": True,
            "enqueue": False,
        },
        LogProfile.DEVELOPMENT: {
            "console_level": "DEBUG",
            "file_level": "INFO",
            "rotation": "100 MB",
            "retention": "7 days",
            "compression": "zip",
            "serialize": False,
            "backtrace": True,
            "diagnose": True,
            "enqueue": True,
        },
        LogProfile.STAGING: {
            "console_level": "INFO",
            "file_level": "INFO",
            "rotation": "500 MB",
            "retention": "14 days",
            "compression": "zip",
            "serialize": True,
            "backtrace": True,
            "diagnose": False,
            "enqueue": True,
        },
        LogProfile.PRODUCTION: {
            "console_level": "DEBUG",
            "file_level": "INFO",
            "rotation": "50 MB",
            "retention": "10 days",
            "compression": "zip",
            # "serialize": True,
            # "backtrace": False,
            # "diagnose": False,
            # "enqueue": True,
            "serialize": False,
            "backtrace": True,
            "diagnose": True,
            "enqueue": True,
        },
    }

    def __init__(self, profile: LogProfile = LogProfile.LOCAL, log_dir: str = "logs"):
        self.profile = profile
        self.log_dir = log_dir
        self.config = self.PROFILE_CONFIGS[profile]

        # Ensure log directory exists (skip for production - no file logging)
        if profile != LogProfile.PRODUCTION:
            os.makedirs(self.log_dir, exist_ok=True)

    def get_format(self, include_color: bool = False) -> str:
        """Generate log format string with context variables"""
        if include_color:
            # Colorized format for console
            return (
                "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
                "<level>{level: <8}</level> | "
                "<cyan>{extra[request_id]}</cyan> | "
                "<yellow>{extra[user_id]}</yellow> | "
                "<magenta>T:{thread.id}</magenta> | "
                "<blue>{name}:{function}:{line}</blue> | "
                "<level>{message}</level>"
            )
        else:
            # Plain format for file logging
            if self.config["serialize"]:
                # JSON format for production environments
                return "{message}"
            else:
                return (
                    "{time:YYYY-MM-DD HH:mm:ss.SSS} | "
                    "{level: <8} | "
                    "ReqID:{extra[request_id]} | "
                    "UserID:{extra[user_id]} | "
                    "Thread:{thread.id} | "
                    "{name}:{function}:{line} | "
                    "{message}"
                )


def patch_record(record):
    """Patch log record with context variables"""
    record["extra"]["request_id"] = request_id_var.get() or "N/A"
    record["extra"]["user_id"] = user_id_var.get() or "N/A"
    return record


def setup_logging(profile: Optional[LogProfile] = None, log_dir: str = "logs", app_name: str = "sahiloan") -> None:
    """
    Setup production-ready logging configuration

    Args:
        profile: Logging profile (local, development, staging, production)
        log_dir: Directory for log files
        app_name: Application name for log file naming
    """
    # Determine profile from environment if not specified
    if profile is None:
        env = os.getenv("ENVIRONMENT", "local").lower()
        try:
            profile = LogProfile(env)
        except ValueError:
            profile = LogProfile.LOCAL
            print(f"Warning: Invalid ENVIRONMENT '{env}', defaulting to 'local'")

    # Initialize configuration
    config = LogConfig(profile=profile, log_dir=log_dir)

    # Remove default handler
    logger.remove()

    # Configure logger with context variables
    logger.configure(patcher=patch_record)

    # Add console handler (stdout)
    logger.add(
        sys.stdout,
        format=config.get_format(include_color=True),
        level=config.config["console_level"],
        colorize=True,
        backtrace=config.config["backtrace"],
        diagnose=config.config["diagnose"],
        enqueue=config.config["enqueue"],
    )

    # Add file handler for all logs (skip for production - console only)
    if profile != LogProfile.PRODUCTION:
        log_file_path = os.path.join(config.log_dir, f"{app_name}.log")
        logger.add(
            log_file_path,
            format=config.get_format(include_color=False),
            level=config.config["file_level"],
            rotation=config.config["rotation"],
            retention=config.config["retention"],
            compression=config.config["compression"],
            backtrace=config.config["backtrace"],
            diagnose=config.config["diagnose"],
            enqueue=config.config["enqueue"],
            serialize=config.config["serialize"],
        )

    # Add separate error log file for staging environment only
    if profile == LogProfile.STAGING:
        error_log_path = os.path.join(config.log_dir, f"{app_name}_error.log")
        logger.add(
            error_log_path,
            format=config.get_format(include_color=False),
            level="ERROR",
            rotation=config.config["rotation"],
            retention=config.config["retention"],
            compression=config.config["compression"],
            backtrace=config.config["backtrace"],
            diagnose=config.config["diagnose"],
            enqueue=config.config["enqueue"],
            serialize=config.config["serialize"],
        )

    logger.info(f"Logging initialized with profile: {profile.value}")


# Context managers for setting request/user context
class LogContext:
    """Context manager for setting logging context variables"""

    @staticmethod
    def set_request_id(request_id: Optional[str] = None) -> str:
        """Set request ID in context (generates UUID if not provided)"""
        if request_id is None:
            request_id = str(uuid.uuid4())
        request_id_var.set(request_id)
        return request_id

    @staticmethod
    def set_user_id(user_id: str) -> None:
        """Set user ID in context"""
        user_id_var.set(user_id)

    @staticmethod
    def clear():
        """Clear all context variables"""
        request_id_var.set(None)
        user_id_var.set(None)

    def __init__(self, request_id: Optional[str] = None, user_id: Optional[str] = None):
        self.request_id = request_id
        self.user_id = user_id
        self._token_request = None
        self._token_user = None

    def __enter__(self):
        if self.request_id:
            self._token_request = request_id_var.set(self.request_id)
        else:
            self._token_request = request_id_var.set(str(uuid.uuid4()))

        if self.user_id:
            self._token_user = user_id_var.set(self.user_id)

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._token_request:
            request_id_var.reset(self._token_request)
        if self._token_user:
            user_id_var.reset(self._token_user)
