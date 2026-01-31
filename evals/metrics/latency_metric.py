from opik.evaluation.metrics import BaseMetric, score_result
from opik.message_processing.emulation.models import SpanModel


class LatencyMetric(BaseMetric):
    """
    Metric that evaluates execution latency/performance.
    Opik automatically tracks latency, but this metric provides scoring.
    """

    def __init__(self, name: str = "latency_score", fast_threshold: float = 2.0, slow_threshold: float = 5.0):
        self.name = name
        self.fast_threshold = fast_threshold
        self.slow_threshold = slow_threshold

    def score(self, task_span: SpanModel, **kwargs) -> score_result.ScoreResult:
        if task_span.start_time and task_span.end_time:
            duration = (task_span.end_time - task_span.start_time).total_seconds()

            # Score based on latency (lower is better)
            if duration < self.fast_threshold:
                score = 1.0
                reason = f"Excellent latency: {duration:.3f}s"
            elif duration < self.slow_threshold:
                score = 0.8 - (duration - self.fast_threshold) / (self.slow_threshold - self.fast_threshold) * 0.3
                reason = f"Good latency: {duration:.3f}s"
            else:
                score = max(0.0, 0.5 - (duration - self.slow_threshold) / self.slow_threshold * 0.5)
                reason = f"Slow latency: {duration:.3f}s"
        else:
            score = 0.0
            reason = "Latency data unavailable"
            duration = None

        return score_result.ScoreResult(value=float(score), name=self.name, reason=reason)
