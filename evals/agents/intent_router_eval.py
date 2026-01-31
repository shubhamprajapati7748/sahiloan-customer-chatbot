import uuid

import opik
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.memory import MemorySaver
from opik.evaluation import evaluate
from opik.evaluation.metrics import Equals
from opik.integrations.langchain import OpikTracer

from evals.create_dataset import get_and_create_dataset
from evals.metrics import CostEfficiencyMetric, LatencyMetric
from sahiloan_chatbot.application.agent.workflow.graph import create_intent_router_graph
from sahiloan_chatbot.application.agent.workflow.state import ChatState
from sahiloan_chatbot.config import settings
from sahiloan_chatbot.logger import logger

checkpointer = MemorySaver()
graph_builder = create_intent_router_graph()
graph = graph_builder.compile(checkpointer)


EXPERIMENT_NAME = "intent_router_experiment"
PROJECT_NAME = "intent_router_evaluation"
DATASET_NAME = "intent_router_dataset"


@opik.track(name="agent_evaluator")
def agent_evaluator(item: dict) -> dict:
    """
    Agent evaluator function that evaluates the Agent.
    This function is tracked by Opik for latency, cost, and performance monitoring.
    """
    try:
        # logger.info(f"Evaluating item: {item}")
        thread_id = uuid.uuid4()
        state = ChatState(messages=[HumanMessage(content=item["input"])])  # pyright: ignore[reportGeneralTypeIssues, reportCallIssue]
        opik_tracer = OpikTracer(graph=graph.get_graph(xray=True), project_name=PROJECT_NAME)
        config = {"configurable": {"thread_id": str(thread_id)}, "callbacks": [opik_tracer]}
        response = graph.invoke(state, config=config)  # pyright: ignore[reportGeneralTypeIssues, reportArgumentType]
        logger.info(f"AgentResponse: {response}")
        return {"output": response.get("route_to") if response.get("route_to") else "error"}  # pyright: ignore[reportOptionalSubscript]
    except Exception as e:
        logger.exception(f"Error in agent: {e}")
        return {"output": "error", "error": str(e)}


# Evals Dataset
dataset = get_and_create_dataset(
    name=DATASET_NAME,
    description="Comprehensive kg graph evaluation dataset with multiple test cases",
    dataset_path=settings.INTENT_ROUTER_EVAL_DATASET_PATH,
)

# Metrics
equals_metric = Equals()
cost_metric = CostEfficiencyMetric()
latency_metric = LatencyMetric(fast_threshold=0.5, slow_threshold=1.0)

## Run evaluation for each model
logger.info(f"{'=' * 60}")
logger.info("Evaluating: Intent Router")
logger.info(f"{'=' * 60}")
try:
    evaluation = evaluate(
        experiment_name=EXPERIMENT_NAME,
        project_name=PROJECT_NAME,
        task=agent_evaluator,
        dataset=dataset,
        task_threads=1,
        scoring_metrics=[equals_metric, latency_metric, cost_metric],
    )
except Exception as e:
    logger.error(f"Error evaluating Agent: {e}")

logger.info(f"{'=' * 60}")
logger.info("Intent Router evaluations completed")
logger.info(f"{'=' * 60}")
