from sahiloan_chatbot.infrastructure.llm_providers.llm_factory import LLMFactory
from functools import lru_cache
from .state import ChatState
from .constants import AGENT_ERROR_MESSAGE
from langchain_core.messages import AIMessage
from sahiloan_chatbot import logger
import time

@lru_cache(maxsize=1)
class Nodes:
    def __init__(self):
        self.llm_factory = LLMFactory()

    def intent_router(self, state: ChatState) -> ChatState:
        try:
            node_start = time.perf_counter()
            logger.info("intent_router_started")
            logger.debug(f"intent_router_state: {state}")
            user_message = state["messages"][-1].content
            # functionality for intent routing
            llm_fact = self.llm_factory.get_gpt_4o_mini()
            response = llm_fact["llm"].invoke(user_message)
            logger.debug(f"intent_router_response: {response.content}")
            latency = (time.perf_counter() - node_start) * 1000
            logger.info(f"intent_router_completed | latency: {latency:.2f}ms | llm : {llm_fact['model_name']}")
            return {
                "route_to": "general_agent",
                "response_type": "text",
            }
        except Exception as e:
            logger.exception(f"intent_router_error: | type: {type(e).__name__} | message: {str(e)}")
            return self._agent_end_state(AGENT_ERROR_MESSAGE)
    
    def general_agent(self, state: ChatState) -> ChatState:
        pass

    def loan_agent(self, state: ChatState) -> ChatState:
        pass
    
    def document_agent(self, state: ChatState) -> ChatState:
        pass


    def _agent_end_state(self, message: str = AGENT_ERROR_MESSAGE) -> ChatState:
        """Returns the agent error state for recommendation related nodes"""
        return {
            "route_to": "end",
            "response_type": "text",
            "messages": [AIMessage(content=message)],
        }
