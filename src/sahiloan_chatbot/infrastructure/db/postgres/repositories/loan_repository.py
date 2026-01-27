"""Repository for UserLoan model operations."""

from datetime import date
from typing import List, Optional
from uuid import UUID

from sqlalchemy import and_
from sqlalchemy.orm import Session

from ..models.user_loan import UserLoan
from .base import BaseRepository


class LoanRepository(BaseRepository[UserLoan]):
    """
    Repository for UserLoan model with domain-specific operations.

    Extends BaseRepository with UserLoan-specific query methods.
    """

    def __init__(self, db: Session):
        """Initialize LoanRepository with UserLoan model."""
        super().__init__(UserLoan, db)

    def get_by_loan_id(self, loan_id: str) -> Optional[UserLoan]:
        """
        Get a loan by loan_id.

        Args:
            loan_id: Unique loan identifier

        Returns:
            UserLoan instance or None if not found
        """
        return self.db.query(UserLoan).filter(UserLoan.loan_id == loan_id).first()

    def get_by_user_id(self, user_id: UUID, skip: int = 0, limit: int = 100) -> List[UserLoan]:
        """
        Get all loans for a specific user.

        Args:
            user_id: User UUID
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of UserLoan instances for the user
        """
        return self.db.query(UserLoan).filter(UserLoan.user_id == user_id).offset(skip).limit(limit).all()

    def get_by_status(self, status: str, skip: int = 0, limit: int = 100) -> List[UserLoan]:
        """
        Get loans by status.

        Args:
            status: UserLoan status (e.g., 'active', 'closed', 'overdue')
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of UserLoan instances with the specified status
        """
        return self.db.query(UserLoan).filter(UserLoan.status == status).offset(skip).limit(limit).all()

    def get_by_user_and_status(self, user_id: UUID, status: str, skip: int = 0, limit: int = 100) -> List[UserLoan]:
        """
        Get loans for a user filtered by status.

        Args:
            user_id: User UUID
            status: UserLoan status
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of UserLoan instances matching the criteria
        """
        return (
            self.db.query(UserLoan)
            .filter(and_(UserLoan.user_id == user_id, UserLoan.status == status))
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_overdue_loans(self, current_date: Optional[date] = None, skip: int = 0, limit: int = 100) -> List[UserLoan]:
        """
        Get loans that are overdue (due_date < current_date and status != 'closed').

        Args:
            current_date: Date to compare against (defaults to today)
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of overdue UserLoan instances
        """
        if current_date is None:
            current_date = date.today()

        return (
            self.db.query(UserLoan)
            .filter(and_(UserLoan.due_date < current_date, UserLoan.status != "closed"))
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_loans_by_type(self, loan_type: str, skip: int = 0, limit: int = 100) -> List[UserLoan]:
        """
        Get loans by loan type.

        Args:
            loan_type: Type of loan (e.g., 'personal', 'home', 'car')
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of UserLoan instances of the specified type
        """
        return self.db.query(UserLoan).filter(UserLoan.loan_type == loan_type).offset(skip).limit(limit).all()

    def get_loans_by_lender(self, lender_name: str, skip: int = 0, limit: int = 100) -> List[UserLoan]:
        """
        Get loans by lender name.

        Args:
            lender_name: Name of the lender
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of UserLoan instances from the specified lender
        """
        return self.db.query(UserLoan).filter(UserLoan.lender_name == lender_name).offset(skip).limit(limit).all()

    def loan_id_exists(self, loan_id: str) -> bool:
        """
        Check if a loan with the given loan_id exists.

        Args:
            loan_id: UserLoan identifier to check

        Returns:
            True if loan_id exists, False otherwise
        """
        return self.db.query(UserLoan).filter(UserLoan.loan_id == loan_id).first() is not None

    def get_total_loan_amount_by_user(self, user_id: UUID) -> float:
        """
        Calculate total loan amount for a user (sum of all active loans).

        Args:
            user_id: User UUID

        Returns:
            Total loan amount as float
        """
        result = (
            self.db.query(UserLoan)
            .filter(and_(UserLoan.user_id == user_id, UserLoan.status != "closed"))
            .with_entities(UserLoan.loan_amount)
            .all()
        )
        return sum(float(amount[0]) for amount in result) if result else 0.0

    def get_total_remaining_amount_by_user(self, user_id: UUID) -> float:
        """
        Calculate total remaining loan amount for a user.

        Args:
            user_id: User UUID

        Returns:
            Total remaining amount as float
        """
        result = (
            self.db.query(UserLoan)
            .filter(and_(UserLoan.user_id == user_id, UserLoan.status != "closed"))
            .with_entities(UserLoan.remaining_amount)
            .all()
        )
        return sum(float(amount[0]) for amount in result) if result else 0.0
