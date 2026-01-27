import time
from functools import lru_cache

from langchain.messages import AIMessage, ToolMessage
from langchain_openai import OpenAIEmbeddings

from sahiloan_chatbot import logger, settings
from sahiloan_chatbot.domain.prompts import (
    GENERAL_AGENT_SYSTEM_PROMPT,
    INTENT_ROUTER_SYSTEM_PROMPT,
    LOAN_AGENT_PROMPT,
)
from sahiloan_chatbot.domain.tools import get_user_loans_tool
from sahiloan_chatbot.infrastructure.db.pine_cone import get_pinecone_index
from sahiloan_chatbot.infrastructure.llm_providers import LLMFactory

from .constants import AGENT_ERROR_MESSAGE
from .schema import RouterSchema
from .state import ChatState


@lru_cache(maxsize=1)
class Nodes:
    def __init__(self):
        self.llm_factory = LLMFactory()
        self.pinecone_index = get_pinecone_index()
        self.embeddings = OpenAIEmbeddings(
            model=settings.EMBEDDING_MODEL,
            dimensions=settings.EMBEDDING_DIMENSIONS,
            api_key=settings.OPENAI_API_KEY.get_secret_value(),
        )

    def intent_router(self, state: ChatState) -> ChatState:
        node_start = time.perf_counter()
        logger.info("intent_router_started")
        try:
            user_message = state["messages"][-1].content
            logger.debug(f"user_message: {user_message}")

            system_msg = [
                {
                    "role": "system",
                    "content": INTENT_ROUTER_SYSTEM_PROMPT.prompt,
                },
                {
                    "role": "user",
                    "content": user_message,
                },
            ]

            # Get LLM and invoke
            llm_fact = self.llm_factory.get_gpt_4o_mini()
            llm_structured = llm_fact["llm"].with_structured_output(RouterSchema)
            response = llm_structured.invoke(system_msg)
            logger.debug(f"llm used : {llm_fact['model_name']} | response: {response.model_dump_json()}")

            state["route_to"] = response.route_to
            latency = (time.perf_counter() - node_start) * 1000
            logger.info(f"intent_router_completed | latency: {latency:.2f}ms")
            return state
        except Exception as e:
            logger.exception(f"intent_router_error: | type: {type(e).__name__} | message: {str(e)}")
            state["route_to"] = "general_agent"
            return state

    def general_agent(self, state: ChatState) -> ChatState:
        node_start = time.perf_counter()
        logger.info("general_agent_started")
        try:
            user_message = state["messages"][-1].content
            logger.debug(f"user_message: {user_message}")

            retrieved_context = self._retrieve_context(user_message)
            if retrieved_context:
                context = "\n\n---\n\n".join(retrieved_context)
                user_content = f"""Context from knowledge base: {context}\n\n
                User Query: {user_message}
                Please answer the user's question using the context provided above. Be helpful and concise."""
            else:
                user_content = f"User Query: {user_message} \n\n Note: No specific information was found in the knowledge base. Please provide a helpful general response."

            system_msg = [
                {
                    "role": "system",
                    "content": GENERAL_AGENT_SYSTEM_PROMPT.prompt,
                },
                {
                    "role": "user",
                    "content": user_content,
                },
            ]

            llm_fact = self.llm_factory.get_gpt_4o_mini()
            response = llm_fact["llm"].invoke(system_msg)
            logger.debug(f"llm used : {llm_fact['model_name']} | response: {response}")
            state["messages"].append(AIMessage(content=response.content))
            state["route_to"] = "end"
            latency = (time.perf_counter() - node_start) * 1000
            logger.info(f"general_agent_completed | latency: {latency:.2f}ms")
            return state
        except Exception as e:
            logger.exception(f"general_agent_error: | type: {type(e).__name__} | message: {str(e)}")
            return self._agent_end_state(state)

    def _retrieve_context(self, user_message: str):
        try:
            logger.debug("Fetching context from Pinecone...")
            query_embedding = self.embeddings.embed_query(user_message)

            # Search Pinecone for top relevant chunks
            search_results = self.pinecone_index.query(
                vector=query_embedding,
                top_k=5,  # Get top 5 relevant chunks
                include_metadata=True,
            )

            context_chunks = []
            for match in search_results["matches"]:
                if match["score"] > 0.5:
                    context_chunks.append(match["metadata"]["text"])

            logger.debug(f"Retrieved {len(context_chunks)} relevant chunks")
            return context_chunks
        except Exception as e:
            logger.exception(f"retrieve_context_error: | type: {type(e).__name__} | message: {str(e)}")
            return []

    def _agent_end_state(self, state: ChatState, message: str = AGENT_ERROR_MESSAGE) -> ChatState:
        state["messages"].append(AIMessage(content=message))
        state["route_to"] = "end"
        return state

    def loan_agent(self, state: ChatState) -> ChatState:
        try:
            node_start = time.perf_counter()
            logger.info("loan_agent_started")
            logger.debug(f"current state: {state}")

            user_id = state["user"].user_id
            user_message = state["messages"][-1].content
            logger.debug(f"user_message: {user_message} | user_id: {user_id}")

            system_msg = [
                {
                    "role": "system",
                    "content": LOAN_AGENT_PROMPT.prompt,
                },
                {
                    "role": "user",
                    "content": f"UserId: {user_id}\nUser Message: {user_message}",
                },
            ]

            llm_fact = self.llm_factory.get_gpt_4o_mini()
            llm_with_tools = llm_fact["llm"].bind_tools([get_user_loans_tool])
            response = llm_with_tools.invoke(system_msg)
            logger.debug(f"llm_response: {response}")

            state["messages"].append(response)
            state["route_to"] = "end"
            latency = (time.perf_counter() - node_start) * 1000
            logger.info(f"loan_agent_completed | latency: {latency:.2f}ms | llm: {llm_fact['model_name']}")
            return state
        except Exception as e:
            logger.exception(f"loan_agent_error: | type: {type(e).__name__} | message: {str(e)}")
            return self._agent_end_state(state)

    def tool_node(self, state: ChatState) -> ChatState:
        logger.info("tool_node_started")
        node_start = time.perf_counter()
        tools_by_name = {tool.name: tool for tool in [get_user_loans_tool]}
        result = []

        # Get the last message (contains tool_calls from LLM)
        last_message = state["messages"][-1]

        # Execute each tool call
        for tool_call in last_message.tool_calls:
            tool = tools_by_name[tool_call["name"]]
            observation = tool.invoke(tool_call["args"])
            logger.debug(f"tool args: {tool_call['args']}")
            result.append(ToolMessage(content=str(observation), tool_call_id=tool_call["id"]))
            logger.debug(f"tool_result: {result}")

        state["messages"].extend(result)
        state["route_to"] = "loan_agent"
        latency = (time.perf_counter() - node_start) * 1000
        logger.info(f"tool_node_completed | latency: {latency:.2f}ms")
        return state

    def document_agent(self, state: ChatState) -> ChatState:
        return state
