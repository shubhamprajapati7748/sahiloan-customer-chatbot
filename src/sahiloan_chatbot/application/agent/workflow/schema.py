from typing import Literal, Optional

from pydantic import BaseModel, Field


class UserSchema(BaseModel):
    user_id: str
    username: str
    first_name: str
    last_name: str


class RouterSchema(BaseModel):
    route_to: Literal["general_agent", "loan_agent", "document_agent", "end"] = Field(
        default="general_agent", description="The next node to route to"
    )

class DocumentSchema(BaseModel):
    document_path: Optional[str] = Field(default=None, description="The path to the document")
    document_analysis: Optional[str] = Field(default=None, description="The analysis of the document")
