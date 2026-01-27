import time
from typing import List, Optional

from langchain.tools import tool
from pydantic import BaseModel, Field

from sahiloan_chatbot import logger
from sahiloan_chatbot.application.services import ServiceFactory
from sahiloan_chatbot.domain.exceptions import ValidationError
from sahiloan_chatbot.infrastructure.db.postgres import get_db_session


class GetUserLoansInput(BaseModel):
    user_id: str = Field(..., description="UUID of the user")
    loan_type: Optional[str] = Field(
        None, description="Type of loan (e.g. Home Loan, Loan Against Property, Personal Loan, Gold Loan)"
    )
    status: Optional[str] = Field(None, description="Loan status (e.g. active, closed)")


@tool(
    "get_user_loans_tool",
    args_schema=GetUserLoansInput,
    description="Fetch all loans for a user. Optionally filter by loan type and loan status.",
)
def get_user_loans_tool(user_id: str, loan_type: Optional[str] = None, status: Optional[str] = None) -> List[dict]:
    """
    Returns a list of loans for a user in JSON format.
    """
    logger.info(f"tool_called: get_user_loans_tool | user_id: {user_id} | loan_type: {loan_type} | status: {status}")
    start_time = time.perf_counter()
    with get_db_session() as db:
        try:
            factory = ServiceFactory(db)
            loan_service = factory.get_loan_service()
            loans = loan_service.get_user_loans(user_id, loan_type, status)
            result = [loan.to_dict() for loan in loans] if loans else []
            latency = (time.perf_counter() - start_time) * 1000
            logger.info(f"tool_completed: get_user_loans_tool | loan_count: {len(result)} | latency: {latency:.2f}ms")
            return result

        except ValidationError as e:
            logger.exception(f"get_user_loans_validation_error | message={str(e)}")
            return [{"error": "ValidationError", "message": str(e)}]

        except Exception as e:
            logger.exception(f"get_user_loans_internal_error | type={type(e).__name__} | message={str(e)}")
            return [{"error": "InternalError", "message": "Something went wrong while fetching loans."}]
