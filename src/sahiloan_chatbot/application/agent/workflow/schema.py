from typing import Literal

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
