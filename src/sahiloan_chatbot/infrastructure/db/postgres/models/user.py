from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..base import Base

if TYPE_CHECKING:
    from .user_loan import UserLoan


class User(Base):
    __tablename__ = "users"

    first_name: Mapped[str | None] = mapped_column(String(100))
    last_name: Mapped[str | None] = mapped_column(String(100))

    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)

    phone_number: Mapped[str] = mapped_column(String(15), nullable=False, unique=True, index=True)

    # relationship with UserLoan
    loans: Mapped[list["UserLoan"]] = relationship("UserLoan", back_populates="user", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": str(self.id),
            "first_name": self.first_name,
            "last_name": self.last_name,
            "email": self.email,
            "phone_number": self.phone_number,
        }
