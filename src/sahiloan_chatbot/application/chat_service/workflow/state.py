from typing import Literal, Optional
from pydantic import BaseModel, Field
from langgraph.graph import MessagesState
from .schema import UserSchema

class ChatState(MessagesState):
    route_to : Literal['general_agent', 'loan_agent', "document_agent", "end"] = Field(default="general_agent", description="The next node to route to")
    response_type : Literal['text', 'audio'] = Field(default="text", description="The type of response to generate")
    user : Optional[UserSchema] = Field(default=None, description="The user schema")
    clarification_count : int = Field(default=0, description="The number of times the clarification has been asked")