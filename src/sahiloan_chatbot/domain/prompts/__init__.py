"""
Prompts module for Sahiloan chatbot.
"""

from .general_agent_prompt import GENERAL_AGENT_SYSTEM_PROMPT
from .intent_router_prompt import INTENT_ROUTER_SYSTEM_PROMPT
from .loan_agent_prompt import LOAN_AGENT_PROMPT

__all__ = [
    "INTENT_ROUTER_SYSTEM_PROMPT",
    "GENERAL_AGENT_SYSTEM_PROMPT",
    "LOAN_AGENT_PROMPT",
]
