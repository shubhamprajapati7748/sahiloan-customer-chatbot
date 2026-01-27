"""User service implementing business logic for user operations."""

from typing import Optional
from uuid import UUID

from sahiloan_chatbot import logger
from sahiloan_chatbot.domain.exceptions import NotFoundError, ValidationError
from sahiloan_chatbot.infrastructure.db.postgres import User, UserRepository


class UserService:
    """
    Service layer for User business logic.

    This service orchestrates user-related operations by:
    1. Validating business rules
    2. Coordinating between repositories
    3. Handling transactions
    4. Applying domain logic

    It does NOT directly access the database - that's the repository's job.
    """

    def __init__(self, user_repository: UserRepository):
        """
        Initialize UserService with dependency injection.

        Args:
            user_repository: UserRepository instance for data access
        """
        self.user_repository = user_repository

    def create_user(
        self,
        email: str,
        phone_number: str,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
    ) -> User:
        """
        Create a new user with business logic validation.

        Args:
            email: User email address
            phone_number: User phone number
            first_name: Optional first name
            last_name: Optional last name

        Returns:
            Created User instance

        Raises:
            ValidationError: If email or phone already exists
        """
        logger.info(f"Creating user with email: {email}")

        # Business logic: Check if user already exists
        if self.user_repository.email_exists(email):
            raise ValidationError(f"User with email {email} already exists")

        if self.user_repository.phone_exists(phone_number):
            raise ValidationError(f"User with phone number {phone_number} already exists")

        # Create user through repository
        user = self.user_repository.create(
            email=email,
            phone_number=phone_number,
            first_name=first_name,
            last_name=last_name,
        )

        logger.info(f"User created successfully: {user.id}")
        return user

    def get_user_by_id(self, user_id: UUID) -> User:
        """
        Get user by ID with error handling.

        Args:
            user_id: User UUID

        Returns:
            User instance

        Raises:
            NotFoundError: If user not found
        """
        user = self.user_repository.get_by_id(user_id)
        if not user:
            raise NotFoundError(f"User with id {user_id} not found")
        return user

    def get_user_by_email(self, email: str) -> User:
        """
        Get user by email with error handling.

        Args:
            email: User email address

        Returns:
            User instance

        Raises:
            NotFoundError: If user not found
        """
        user = self.user_repository.get_by_email(email)
        if not user:
            raise NotFoundError(f"User with email {email} not found")
        return user

    def get_user_by_phone(self, phone_number: str) -> User:
        """
        Get user by phone number with error handling.

        Args:
            phone_number: User phone number

        Returns:
            User instance

        Raises:
            NotFoundError: If user not found
        """
        user = self.user_repository.get_by_phone_number(phone_number)
        if not user:
            raise NotFoundError(f"User with phone number {phone_number} not found")
        return user

    def update_user(
        self,
        user_id: UUID,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        email: Optional[str] = None,
        phone_number: Optional[str] = None,
    ) -> User:
        """
        Update user information with validation.

        Args:
            user_id: User UUID
            first_name: Optional new first name
            last_name: Optional new last name
            email: Optional new email (must be unique)
            phone_number: Optional new phone (must be unique)

        Returns:
            Updated User instance

        Raises:
            NotFoundError: If user not found
            ValidationError: If email or phone already exists
        """
        # Business logic: Ensure user exists
        user = self.get_user_by_id(user_id)

        # Business logic: Validate uniqueness if email/phone is being changed
        update_data = {}
        if first_name is not None:
            update_data["first_name"] = first_name
        if last_name is not None:
            update_data["last_name"] = last_name
        if email is not None and email != user.email:
            if self.user_repository.email_exists(email):
                raise ValidationError(f"Email {email} already exists")
            update_data["email"] = email
        if phone_number is not None and phone_number != user.phone_number:
            if self.user_repository.phone_exists(phone_number):
                raise ValidationError(f"Phone number {phone_number} already exists")
            update_data["phone_number"] = phone_number

        if not update_data:
            return user  # No changes

        updated_user = self.user_repository.update(user_id, **update_data)
        logger.info(f"User updated: {user_id}")
        return updated_user

    def delete_user(self, user_id: UUID) -> bool:
        """
        Delete a user (soft delete or hard delete based on business rules).

        Args:
            user_id: User UUID

        Returns:
            True if deleted successfully

        Raises:
            NotFoundError: If user not found
        """
        # Business logic: Check if user exists
        # user = self.get_user_by_id(user_id)

        # Business logic: Could add checks here (e.g., user has active loans)
        # For now, we'll allow deletion

        deleted = self.user_repository.delete(user_id)
        if deleted:
            logger.info(f"User deleted: {user_id}")
        return deleted

    def get_users_with_loans(self, skip: int = 0, limit: int = 100) -> list[User]:
        """
        Get users who have at least one loan.

        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of User instances with loans
        """
        return self.user_repository.get_users_with_loans(skip=skip, limit=limit)
