from typing import Any, Dict

from opik.evaluation.metrics import BaseMetric, score_result
from opik.message_processing.emulation.models import SpanModel


class CostEfficiencyMetric(BaseMetric):
    """
    Metric that evaluates cost efficiency based on token usage and actual cost.
    """

    def __init__(self, name: str = "cost_efficiency"):
        super().__init__(name)

    def _analyze_cost_recursively(self, span: SpanModel) -> Dict[str, Any]:
        """Recursively analyze cost and token usage across the span tree."""
        stats = {
            "input_tokens": 0,
            "output_tokens": 0,
            "total_tokens": 0,
            "total_cost": 0.0,
            "llm_calls": 0,
            "models_used": set(),
            "providers": set(),
        }

        # Check if this is an LLM span
        if span.type == "llm":
            stats["llm_calls"] += 1

            # Track model and provider
            if span.model:
                stats["models_used"].add(span.model)
            if span.provider:
                stats["providers"].add(span.provider)

            # Method 1: Check usage dictionary
            if span.usage and isinstance(span.usage, dict):
                stats["input_tokens"] += span.usage.get("prompt_tokens", 0) or span.usage.get("input_tokens", 0) or 0
                stats["output_tokens"] += (
                    span.usage.get("completion_tokens", 0) or span.usage.get("output_tokens", 0) or 0
                )
                stats["total_tokens"] += span.usage.get("total_tokens", 0) or (
                    stats["input_tokens"] + stats["output_tokens"]
                )

            # Method 2: Check metadata for token usage
            if span.metadata and isinstance(span.metadata, dict):
                token_data = span.metadata.get("token_usage", {})
                if isinstance(token_data, dict):
                    stats["input_tokens"] += (
                        token_data.get("prompt_tokens", 0) or token_data.get("input_tokens", 0) or 0
                    )
                    stats["output_tokens"] += (
                        token_data.get("completion_tokens", 0) or token_data.get("output_tokens", 0) or 0
                    )
                    stats["total_tokens"] += token_data.get("total_tokens", 0) or 0

            # Get cost from current span
            if hasattr(span, "total_cost") and span.total_cost is not None:
                stats["total_cost"] += span.total_cost

        # Recursively check nested spans
        for nested_span in span.spans:
            nested_stats = self._analyze_cost_recursively(nested_span)
            stats["input_tokens"] += nested_stats["input_tokens"]
            stats["output_tokens"] += nested_stats["output_tokens"]
            stats["total_tokens"] += nested_stats["total_tokens"]
            stats["total_cost"] += nested_stats["total_cost"]
            stats["llm_calls"] += nested_stats["llm_calls"]
            stats["models_used"].update(nested_stats["models_used"])
            stats["providers"].update(nested_stats["providers"])

        return stats

    def score(self, task_span: SpanModel, **kwargs) -> score_result.ScoreResult:
        """
        Score based on token usage and cost.
        """
        # Extract cost and token usage from the span tree
        stats = self._analyze_cost_recursively(task_span)

        total_tokens = stats["total_tokens"]
        input_tokens = stats["input_tokens"]
        output_tokens = stats["output_tokens"]
        total_cost = stats["total_cost"]
        llm_calls = stats["llm_calls"]
        models = list(stats["models_used"])
        # providers = list(stats["providers"])

        if total_tokens == 0 and total_cost == 0:
            return score_result.ScoreResult(value=0.0, name=self.name, reason="No token usage or cost data available")

        # Calculate cost per token if both metrics are available
        cost_per_token = total_cost / total_tokens if total_tokens > 0 and total_cost > 0 else None

        # Score based on token usage and cost
        if total_cost > 0:
            # If we have actual cost data, prioritize that
            if total_cost < 0.02:
                score = 1.0
                efficiency = "Highly efficient"
            elif total_cost < 0.10:
                score = 0.8
                efficiency = "Efficient"
            elif total_cost < 0.50:
                score = 0.6
                efficiency = "Moderately efficient"
            else:
                score = 0.4
                efficiency = "Expensive"
        else:
            # Fall back to token-based scoring
            if total_tokens < 2000:
                score = 1.0
                efficiency = "Highly efficient"
            elif total_tokens < 5000:
                score = 0.8
                efficiency = "Efficient"
            elif total_tokens < 10000:
                score = 0.6
                efficiency = "Moderately efficient"
            else:
                score = 0.4
                efficiency = "Expensive"

        # Build detailed reason
        reason = f"{efficiency}: {total_tokens} tokens total ({input_tokens} in, {output_tokens} out)"
        if total_cost > 0:
            reason += f", cost: ${total_cost:.4f}"
        if cost_per_token:
            reason += f", ${cost_per_token:.6f}/token"
        if llm_calls > 1:
            reason += f" across {llm_calls} LLM calls"
        if models:
            reason += f", models: {', '.join(models)}"

        return score_result.ScoreResult(value=float(score), name=self.name, reason=reason)


cost_metric = CostEfficiencyMetric()
