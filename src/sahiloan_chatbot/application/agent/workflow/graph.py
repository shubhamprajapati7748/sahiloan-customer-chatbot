from functools import lru_cache
from typing import Literal

from langgraph.graph import END, START, StateGraph

from .nodes import Nodes
from .state import ChatState

nodes = Nodes()


@lru_cache(maxsize=1)
def create_chat_graph():
    graph_builder = StateGraph[ChatState, None, ChatState, ChatState](ChatState)
    graph_builder.add_node("intent_router", nodes.intent_router)
    graph_builder.add_node("general_agent", nodes.general_agent)
    graph_builder.add_node("loan_agent", nodes.loan_agent)
    graph_builder.add_node("tool_node", nodes.tool_node)
    graph_builder.add_node("document_agent", nodes.document_agent)

    graph_builder.add_edge(START, "intent_router")

    graph_builder.add_conditional_edges(
        "intent_router",
        lambda state: state["route_to"],
        {"general_agent": "general_agent", "loan_agent": "loan_agent", "document_agent": "document_agent", "end": END},
    )

    graph_builder.add_conditional_edges("loan_agent", should_continue, ["tool_node", END])
    graph_builder.add_edge("tool_node", "loan_agent")

    graph_builder.add_edge("general_agent", END)
    graph_builder.add_edge("document_agent", END)

    return graph_builder


@lru_cache(maxsize=1)
def create_intent_router_graph():
    graph_builder = StateGraph[ChatState, None, ChatState, ChatState](ChatState)
    graph_builder.add_node("intent_router", nodes.intent_router)
    graph_builder.add_edge(START, "intent_router")
    graph_builder.add_edge("intent_router", END)
    return graph_builder


def should_continue(state: ChatState) -> Literal["tool_node", END]:  # pyright: ignore[reportInvalidTypeForm]
    """Route to tool node if LLM made tool calls, else end."""
    last_message = state["messages"][-1]
    if last_message.tool_calls:
        return "tool_node"
    return END


@lru_cache(maxsize=1)
def create_loan_agent_graph():
    graph_builder = StateGraph[ChatState, None, ChatState, ChatState](ChatState)
    graph_builder.add_node("loan_agent", nodes.loan_agent)
    graph_builder.add_node("tool_node", nodes.tool_node)
    graph_builder.add_edge(START, "loan_agent")
    graph_builder.add_conditional_edges("loan_agent", should_continue, ["tool_node", END])
    graph_builder.add_edge("tool_node", "loan_agent")
    return graph_builder
