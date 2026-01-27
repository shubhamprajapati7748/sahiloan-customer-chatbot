import uuid
from typing import TYPE_CHECKING

from sqlalchemy import UUID, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..base import Base, SerializerMixin

if TYPE_CHECKING:
    from .user import User


class Loan(Base, SerializerMixin):
    __tablename__ = "loans"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    loan_id: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)

    loan_type: Mapped[str] = mapped_column(String(50), nullable=False)
    lender_name: Mapped[str] = mapped_column(String(150), nullable=False)

    loan_amount: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False)

    remaining_amount: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False)

    interest_rate: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)

    tenure_months: Mapped[int] = mapped_column(Integer, nullable=False)

    emi_amount: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False)

    status: Mapped[str] = mapped_column(String(30), nullable=False, index=True)

    open_date: Mapped[str] = mapped_column(String(100), nullable=False)
    due_date: Mapped[str] = mapped_column(String(100), nullable=False)

    # relationship with User
    user: Mapped["User"] = relationship("User", back_populates="loans")

    def to_dict(self):
        data = {
            "id": self.id,
            "loan_id": self.loan_id,
            "loan_type": self.loan_type,
            "lender_name": self.lender_name,
            "loan_amount": self.loan_amount,
            "remaining_amount": self.remaining_amount,
            "interest_rate": self.interest_rate,
            "tenure_months": self.tenure_months,
            "emi_amount": self.emi_amount,
            "status": self.status,
            "open_date": self.open_date,
            "due_date": self.due_date,
        }
        return {k: self.serialize_value(v) for k, v in data.items()}
