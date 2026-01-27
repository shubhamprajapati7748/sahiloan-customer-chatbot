"""
Repository layer for database operations.

This package contains repository classes that encapsulate
all database CRUD operations following the Repository pattern.
"""

from .base import BaseRepository
from .loan_repository import LoanRepository
from .user_repository import UserRepository

__all__ = ["BaseRepository", "UserRepository", "LoanRepository"]
