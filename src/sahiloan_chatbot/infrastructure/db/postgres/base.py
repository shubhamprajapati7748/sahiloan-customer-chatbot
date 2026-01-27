import uuid

from sqlalchemy import UUID, Column, DateTime
from sqlalchemy.orm import DeclarativeBase

from .datetime_utils import ist_now_naive


class Base(DeclarativeBase):
    """Base class for all models."""

    id = Column(UUID, primary_key=True, default=uuid.uuid4, nullable=False)
    created_at = Column(DateTime, default=ist_now_naive, nullable=False)
    modified_at = Column(DateTime, default=ist_now_naive, onupdate=ist_now_naive, nullable=False)
