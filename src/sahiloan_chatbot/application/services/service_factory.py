"""Service factory for dependency injection and service creation."""

from sqlalchemy.orm import Session

from sahiloan_chatbot.infrastructure.db.postgres import LoanRepository, UserRepository

from .loan_service import LoanService
from .user_service import UserService


class ServiceFactory:
    """
    Factory for creating service instances with proper dependency injection.

    This factory ensures that all services are created with their required
    dependencies (repositories) properly injected.

    Usage:
        factory = ServiceFactory(db_session)
        user_service = factory.get_user_service()
        loan_service = factory.get_loan_service()
    """

    def __init__(self, db: Session):
        """
        Initialize the service factory with a database session.

        Args:
            db: SQLAlchemy database session
        """
        self.db = db
        self._user_repository: UserRepository | None = None
        self._loan_repository: LoanRepository | None = None

    def get_user_repository(self) -> UserRepository:
        """Get or create UserRepository instance."""
        if self._user_repository is None:
            self._user_repository = UserRepository(self.db)
        return self._user_repository

    def get_loan_repository(self) -> LoanRepository:
        """Get or create LoanRepository instance."""
        if self._loan_repository is None:
            self._loan_repository = LoanRepository(self.db)
        return self._loan_repository

    def get_user_service(self) -> UserService:
        """
        Create UserService with dependencies injected.

        Returns:
            UserService instance
        """
        user_repository = self.get_user_repository()
        return UserService(user_repository=user_repository)

    def get_loan_service(self) -> LoanService:
        """
        Create LoanService with dependencies injected.

        Returns:
            LoanService instance
        """
        loan_repository = self.get_loan_repository()
        user_repository = self.get_user_repository()
        return LoanService(
            loan_repository=loan_repository,
            user_repository=user_repository,
        )
