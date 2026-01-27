"""Datetime utilities for consistent timezone handling accross the application"""

from datetime import datetime, timezone
from zoneinfo import ZoneInfo


def ist_now() -> datetime:
    """
    Get current IST time using zoneinfo.
    """
    return datetime.now(ZoneInfo("Asia/Kolkata"))


def ist_now_naive() -> datetime:
    """
    Get current IST time as a naive datetime (no tzinfo).
    """
    return datetime.now(ZoneInfo("Asia/Kolkata")).replace(tzinfo=None)


def utc_now() -> datetime:
    """
    Get current UTC time - standardize across the application.

    Returns:
        Current datetime in UTC timezone.

    Note:
        This replaces datetime.now() and datetime.utcnow() thoughout the codebase.
        to ensure consitent timezone handling.
    """
    return datetime.now(timezone.utc)


def utc_now_naive() -> datetime:
    """
    Get current UTC time as naive datatime for datebase operations.

    Returns:
        Current datetime in UTC as naive datatime (no timezone info).

    Note:
        This is specifically for SQLAlchemy models that uses TIMESTAMPS witout TIME Zone columns. For application logic, use utc_now_naive() instead.
    """
    return datetime.now(timezone.utc).replace(tzinfo=None)
