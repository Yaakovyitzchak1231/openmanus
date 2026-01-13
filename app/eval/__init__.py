"""
Evaluation module for OpenManus agent benchmarks.

Provides task definitions, trial execution, grading, and metrics calculation
for measuring agent performance with pass@k, token efficiency, and more.

Usage:
    from app.eval import EvalTask, TrialRunner, CodeGrader, aggregate_metrics

    task = EvalTask(task_id="test", prompt="Write factorial")
    runner = TrialRunner(graders=[CodeGrader()])
    outcome = await runner.run_trial(task, agent)
    metrics = aggregate_metrics([outcome])
"""

from .task import EvalTask
from .outcome import TrialOutcome, GradeResult
from .grader import BaseGrader, CodeGrader, ModelGrader
from .trial import TrialRunner
from .metrics import calculate_pass_at_k, token_efficiency, success_rate_by_category, aggregate_metrics

__all__ = [
    "EvalTask",
    "TrialOutcome",
    "GradeResult",
    "BaseGrader",
    "CodeGrader",
    "ModelGrader",
    "TrialRunner",
    "calculate_pass_at_k",
    "token_efficiency",
    "success_rate_by_category",
    "aggregate_metrics",
]
