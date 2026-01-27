"""
Database models package.

Import all models here to ensure they are registered with SQLAlchemy Base.
This allows Alembic to discover all models for migrations.
"""

from .user import User
from .user_loan import UserLoan

__all__ = ["User", "UserLoan"]
