"""Repository for User model operations."""

from typing import List, Optional

from sqlalchemy.orm import Session

from ..models import User
from .base import BaseRepository


class UserRepository(BaseRepository[User]):
    """
    Repository for User model with domain-specific operations.

    Extends BaseRepository with User-specific query methods.
    """

    def __init__(self, db: Session):
        """Initialize UserRepository with User model."""
        super().__init__(User, db)

    def get_by_email(self, email: str) -> Optional[User]:
        """
        Get a user by email address.

        Args:
            email: User email address

        Returns:
            User instance or None if not found
        """
        return self.db.query(User).filter(User.email == email).first()

    def get_by_phone_number(self, phone_number: str) -> Optional[User]:
        """
        Get a user by phone number.

        Args:
            phone_number: User phone number

        Returns:
            User instance or None if not found
        """
        return self.db.query(User).filter(User.phone_number == phone_number).first()

    def get_by_email_or_phone(self, email: Optional[str] = None, phone_number: Optional[str] = None) -> Optional[User]:
        """
        Get a user by email or phone number.

        Args:
            email: User email address (optional)
            phone_number: User phone number (optional)

        Returns:
            User instance or None if not found

        Raises:
            ValueError: If neither email nor phone_number is provided
        """
        if not email and not phone_number:
            raise ValueError("Either email or phone_number must be provided")

        query = self.db.query(User)
        if email:
            query = query.filter(User.email == email)
        if phone_number:
            query = query.filter(User.phone_number == phone_number)

        return query.first()

    def get_users_with_loans(self, skip: int = 0, limit: int = 100) -> List[User]:
        """
        Get users who have at least one loan.

        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of User instances with loans
        """
        return self.db.query(User).filter(User.loans.any()).offset(skip).limit(limit).all()

    def email_exists(self, email: str) -> bool:
        """
        Check if a user with the given email exists.

        Args:
            email: Email address to check

        Returns:
            True if email exists, False otherwise
        """
        return self.db.query(User).filter(User.email == email).first() is not None

    def phone_exists(self, phone_number: str) -> bool:
        """
        Check if a user with the given phone number exists.

        Args:
            phone_number: Phone number to check

        Returns:
            True if phone number exists, False otherwise
        """
        return self.db.query(User).filter(User.phone_number == phone_number).first() is not None
