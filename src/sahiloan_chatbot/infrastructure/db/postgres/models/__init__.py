"""
Database models package.

Import all models here to ensure they are registered with SQLAlchemy Base.
This allows Alembic to discover all models for migrations.
"""

from .loan import Loan
from .user import User

__all__ = ["User", "Loan"]
