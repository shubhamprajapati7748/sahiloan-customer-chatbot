from sqlalchemy.orm import Session

from sahiloan_chatbot import logger

from .models import User
from .sessions import SessionLocal, create_tables, drop_tables


def init_db():
    """
    Initialize the database by creating tables and adding initial data.
    """
    try:
        # Drop existing tables to ensure schema is up to date
        # logger.info("Dropping existing database tables.")
        # drop_tables()
        # logger.info("Existing tables dropped successfully!")

        # creates all tables
        logger.info("Creating database tables.")
        create_tables()
        logger.info("Database tables created successfully !")

        # create superuser if it doesn't exist
        db = SessionLocal()

        try:
            # check if superuser already exists
            superuser = db.query(User).filter(User.email == "admin@SahiLoan.com").first()
            if not superuser:
                logger.info("Creating superuser...")
                superuser = User(
                    first_name="Admin user",
                    last_name="Admin user",
                    email="admin@SahiLoan.com",
                    phone_number="9999999999",
                )
                db.add(superuser)
                db.commit()
                logger.info("Superuser created successfully !")
            else:
                logger.info("Superuser already exists !")
        finally:
            db.close()

    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        raise e


def close_db(db: Session):
    """
    Close the database connection.
    """
    db.close()


def drop_db(db: Session):
    """
    Delete all the tables
    """
    drop_tables()
