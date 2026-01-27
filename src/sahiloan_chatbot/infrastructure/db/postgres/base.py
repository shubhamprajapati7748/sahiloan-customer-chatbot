import uuid
from datetime import date, datetime, time
from decimal import Decimal
from enum import Enum

from sqlalchemy import UUID, Column, DateTime
from sqlalchemy.orm import DeclarativeBase

from .datetime_utils import ist_now_naive


class Base(DeclarativeBase):
    """Base class for all models."""

    id = Column(UUID, primary_key=True, default=uuid.uuid4, nullable=False)
    created_at = Column(DateTime, default=ist_now_naive, nullable=False)
    modified_at = Column(DateTime, default=ist_now_naive, onupdate=ist_now_naive, nullable=False)


class SerializerMixin:
    def serialize_value(self, value):
        if value is None:
            return None

        if isinstance(value, Decimal):
            return float(value)

        if isinstance(value, uuid.UUID):
            return str(value)

        if isinstance(value, (datetime, date, time)):
            return value.isoformat()

        if isinstance(value, Enum):
            return value.value

        if isinstance(value, list):
            return [self.serialize_value(v) for v in value]

        if isinstance(value, dict):
            return {k: self.serialize_value(v) for k, v in value.items()}

        return value
