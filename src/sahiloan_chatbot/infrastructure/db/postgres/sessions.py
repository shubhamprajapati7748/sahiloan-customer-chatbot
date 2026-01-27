"""Database session management."""

from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from sahiloan_chatbot import settings

from .base import Base

# # Create database engine
engine = create_engine(
    settings.POSTGRES_URL,
    poolclass=StaticPool,
    pool_pre_ping=True,
)

# Create session factory
SessionLocal = sessionmaker(autoflush=False, autocommit=False, bind=engine)


@contextmanager
def get_db_session() -> Session:
    """
    Dependency to get database session.

    Yields:
        Session: Database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables():
    """
    Create all tables in the database.
    """
    Base.metadata.create_all(bind=engine)


def drop_tables():
    """
    Drop all the tables in the database.
    """
    Base.metadata.drop_all(bind=engine)
