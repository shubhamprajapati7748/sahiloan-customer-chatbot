"""UserLoan service implementing business logic for loan operations."""

from datetime import date
from typing import Optional
from uuid import UUID

from sahiloan_chatbot import logger
from sahiloan_chatbot.domain.exceptions import NotFoundError, ValidationError
from sahiloan_chatbot.infrastructure.db.postgres import LoanRepository, UserLoan, UserRepository


class LoanService:
    """
    Service layer for UserLoan business logic.

    This service orchestrates loan-related operations by:
    1. Validating business rules
    2. Coordinating between repositories (UserLoan + User)
    3. Handling transactions
    4. Applying domain logic (calculations, validations)
    """

    def __init__(
        self,
        loan_repository: LoanRepository,
        user_repository: UserRepository,
    ):
        """
        Initialize LoanService with dependency injection.

        Args:
            loan_repository: LoanRepository instance for data access
            user_repository: UserRepository instance for user validation
        """
        self.loan_repository = loan_repository
        self.user_repository = user_repository

    def create_loan(
        self,
        user_id: UUID,
        loan_id: str,
        loan_type: str,
        lender_name: str,
        loan_amount: float,
        remaining_amount: float,
        interest_rate: float,
        tenure_months: int,
        emi_amount: float,
        status: str,
        open_date: str,
        due_date: str,
    ) -> UserLoan:
        """
        Create a new loan with business logic validation.

        Args:
            user_id: User UUID
            loan_id: Unique loan identifier
            loan_type: Type of loan
            lender_name: Name of lender
            loan_amount: Total loan amount
            remaining_amount: Remaining amount to pay
            interest_rate: Interest rate percentage
            tenure_months: UserLoan tenure in months
            emi_amount: EMI amount
            status: UserLoan status
            open_date: UserLoan opening date
            due_date: UserLoan due date

        Returns:
            Created UserLoan instance

        Raises:
            NotFoundError: If user not found
            ValidationError: If loan_id already exists or validation fails
        """
        logger.info(f"Creating loan {loan_id} for user {user_id}")

        # Business logic: Validate user exists
        user = self.user_repository.get_by_id(user_id)
        if not user:
            raise NotFoundError(f"User with id {user_id} not found")

        # Business logic: Check if loan_id already exists
        if self.loan_repository.loan_id_exists(loan_id):
            raise ValidationError(f"UserLoan with loan_id {loan_id} already exists")

        # Business logic: Validate loan amounts
        if loan_amount <= 0:
            raise ValidationError("UserLoan amount must be greater than 0")
        if remaining_amount < 0:
            raise ValidationError("Remaining amount cannot be negative")
        if remaining_amount > loan_amount:
            raise ValidationError("Remaining amount cannot exceed loan amount")

        # Create loan through repository
        loan = self.loan_repository.create(
            user_id=user_id,
            loan_id=loan_id,
            loan_type=loan_type,
            lender_name=lender_name,
            loan_amount=loan_amount,
            remaining_amount=remaining_amount,
            interest_rate=interest_rate,
            tenure_months=tenure_months,
            emi_amount=emi_amount,
            status=status,
            open_date=open_date,
            due_date=due_date,
        )

        logger.info(f"UserLoan created successfully: {loan.id}")
        return loan

    def get_loan_by_id(self, loan_id: UUID) -> UserLoan:
        """
        Get loan by ID with error handling.

        Args:
            loan_id: UserLoan UUID

        Returns:
            UserLoan instance

        Raises:
            NotFoundError: If loan not found
        """
        loan = self.loan_repository.get_by_id(loan_id)
        if not loan:
            raise NotFoundError(f"UserLoan with id {loan_id} not found")
        return loan

    def get_loan_by_loan_id(self, loan_id: str) -> UserLoan:
        """
        Get loan by loan_id string with error handling.

        Args:
            loan_id: UserLoan identifier string

        Returns:
            UserLoan instance

        Raises:
            NotFoundError: If loan not found
        """
        loan = self.loan_repository.get_by_loan_id(loan_id)
        if not loan:
            raise NotFoundError(f"UserLoan with loan_id {loan_id} not found")
        return loan

    def get_user_loans(
        self,
        user_id: UUID,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[UserLoan]:
        """
        Get loans for a specific user, optionally filtered by status.

        Args:
            user_id: User UUID
            status: Optional status filter
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of UserLoan instances

        Raises:
            NotFoundError: If user not found
        """
        # Business logic: Validate user exists
        user = self.user_repository.get_by_id(user_id)
        if not user:
            raise NotFoundError(f"User with id {user_id} not found")

        if status:
            return self.loan_repository.get_by_user_and_status(user_id=user_id, status=status, skip=skip, limit=limit)
        else:
            return self.loan_repository.get_by_user_id(user_id=user_id, skip=skip, limit=limit)

    def get_overdue_loans(
        self,
        current_date: Optional[date] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[UserLoan]:
        """
        Get loans that are overdue.

        Args:
            current_date: Date to compare against (defaults to today)
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of overdue UserLoan instances
        """
        return self.loan_repository.get_overdue_loans(current_date=current_date, skip=skip, limit=limit)

    def update_loan_status(self, loan_id: UUID, status: str) -> UserLoan:
        """
        Update loan status with business logic validation.

        Args:
            loan_id: UserLoan UUID
            status: New status

        Returns:
            Updated UserLoan instance

        Raises:
            NotFoundError: If loan not found
            ValidationError: If status is invalid
        """
        # loan = self.get_loan_by_id(loan_id)

        # Business logic: Validate status transition (could be more complex)
        valid_statuses = ["active", "closed", "overdue", "pending"]
        if status not in valid_statuses:
            raise ValidationError(f"Invalid status. Must be one of: {valid_statuses}")

        updated_loan = self.loan_repository.update(loan_id, status=status)
        logger.info(f"UserLoan {loan_id} status updated to {status}")
        return updated_loan

    def get_user_loan_summary(self, user_id: UUID) -> dict:
        """
        Get comprehensive loan summary for a user.

        This demonstrates service layer orchestrating multiple repository calls
        and applying business logic.

        Args:
            user_id: User UUID

        Returns:
            Dictionary with loan summary statistics

        Raises:
            NotFoundError: If user not found
        """
        # Business logic: Validate user exists
        user = self.user_repository.get_by_id(user_id)
        if not user:
            raise NotFoundError(f"User with id {user_id} not found")

        # Get all user loans
        loans = self.loan_repository.get_by_user_id(user_id)

        # Business logic: Calculate summary statistics
        total_loan_amount = self.loan_repository.get_total_loan_amount_by_user(user_id)
        total_remaining = self.loan_repository.get_total_remaining_amount_by_user(user_id)

        active_loans = [loan for loan in loans if loan.status == "active"]
        overdue_loans = self.loan_repository.get_overdue_loans()
        user_overdue = [loan for loan in overdue_loans if loan.user_id == user_id]

        return {
            "user_id": str(user_id),
            "total_loans": len(loans),
            "active_loans": len(active_loans),
            "overdue_loans": len(user_overdue),
            "total_loan_amount": float(total_loan_amount),
            "total_remaining_amount": float(total_remaining),
            "total_paid_amount": float(total_loan_amount - total_remaining),
        }
