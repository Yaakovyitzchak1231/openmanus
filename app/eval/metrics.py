"""
Metrics calculation for evaluation results.

Supports:
- pass@k: Probability of at least 1 success in k samples
- Token efficiency: Tokens per successful task
- Category-wise success rates
- Aggregate metrics reports
"""

from typing import List, Dict, Any, TYPE_CHECKING
from collections import defaultdict
from math import comb

if TYPE_CHECKING:
    from app.eval.outcome import TrialOutcome


def calculate_pass_at_k(outcomes: List["TrialOutcome"], k: int) -> float:
    """Calculate pass@k metric.

    pass@k = probability of at least 1 success in k random samples

    Formula: 1 - C(n-c, k) / C(n, k)
    where n = total trials, c = successful trials

    Args:
        outcomes: List of trial outcomes
        k: Number of samples to consider

    Returns:
        Probability between 0.0 and 1.0
    """
    if not outcomes or k <= 0:
        return 0.0

    n = len(outcomes)
    c = sum(1 for o in outcomes if o.passed)

    # If we have fewer samples than k, just return whether any passed
    if n < k:
        return float(c > 0)

    # If all failures would still not fill k samples, pass@k = 1
    if n - c < k:
        return 1.0

    # pass@k = 1 - C(n-c, k) / C(n, k)
    try:
        return 1.0 - comb(n - c, k) / comb(n, k)
    except (ValueError, ZeroDivisionError):
        return 0.0


def token_efficiency(outcomes: List["TrialOutcome"]) -> Dict[str, float]:
    """Calculate token efficiency metrics.

    Args:
        outcomes: List of trial outcomes

    Returns:
        Dict with avg_tokens_per_success, total_tokens, success_count
    """
    if not outcomes:
        return {
            "avg_tokens_per_success": float("inf"),
            "total_tokens": 0,
            "success_count": 0
        }

    successful = [o for o in outcomes if o.passed]
    total_tokens = sum(o.tokens_used for o in outcomes)

    if not successful:
        return {
            "avg_tokens_per_success": float("inf"),
            "total_tokens": total_tokens,
            "success_count": 0
        }

    success_tokens = sum(o.tokens_used for o in successful)
    return {
        "avg_tokens_per_success": success_tokens / len(successful),
        "total_tokens": total_tokens,
        "success_count": len(successful)
    }


def success_rate_by_category(
    outcomes: List["TrialOutcome"],
    tasks: Dict[str, Any]
) -> Dict[str, float]:
    """Calculate success rate per task category.

    Args:
        outcomes: List of trial outcomes
        tasks: Dict mapping task_id to task object/dict

    Returns:
        Dict mapping category name to success rate (0.0-1.0)
    """
    by_category: Dict[str, List[bool]] = defaultdict(list)

    for outcome in outcomes:
        task = tasks.get(outcome.task_id, {})
        if isinstance(task, dict):
            category = task.get("category", "unknown")
        else:
            category = getattr(task, "category", "unknown")
        by_category[category].append(outcome.passed)

    return {
        cat: sum(passes) / len(passes) if passes else 0.0
        for cat, passes in by_category.items()
    }


def success_rate_by_difficulty(
    outcomes: List["TrialOutcome"],
    tasks: Dict[str, Any]
) -> Dict[str, float]:
    """Calculate success rate per difficulty level.

    Args:
        outcomes: List of trial outcomes
        tasks: Dict mapping task_id to task object/dict

    Returns:
        Dict mapping difficulty to success rate (0.0-1.0)
    """
    by_difficulty: Dict[str, List[bool]] = defaultdict(list)

    for outcome in outcomes:
        task = tasks.get(outcome.task_id, {})
        if isinstance(task, dict):
            difficulty = task.get("difficulty", "unknown")
        else:
            difficulty = getattr(task, "difficulty", "unknown")
        by_difficulty[difficulty].append(outcome.passed)

    return {
        diff: sum(passes) / len(passes) if passes else 0.0
        for diff, passes in by_difficulty.items()
    }


def aggregate_metrics(
    outcomes: List["TrialOutcome"],
    tasks: Dict[str, Any] = None
) -> Dict[str, Any]:
    """Generate comprehensive metrics report.

    Args:
        outcomes: List of trial outcomes
        tasks: Optional dict mapping task_id to task for category analysis

    Returns:
        Dict with all metrics
    """
    if not outcomes:
        return {"error": "No outcomes to analyze"}

    tasks = tasks or {}

    passed = sum(1 for o in outcomes if o.passed)
    failed = len(outcomes) - passed

    return {
        # Basic counts
        "total_trials": len(outcomes),
        "passed": passed,
        "failed": failed,

        # Pass rates
        "pass_rate": passed / len(outcomes) if outcomes else 0.0,
        "pass_at_1": calculate_pass_at_k(outcomes, 1),
        "pass_at_3": calculate_pass_at_k(outcomes, 3),
        "pass_at_5": calculate_pass_at_k(outcomes, 5),

        # Scores
        "avg_score": sum(o.final_score for o in outcomes) / len(outcomes),
        "min_score": min(o.final_score for o in outcomes),
        "max_score": max(o.final_score for o in outcomes),

        # Performance
        "avg_steps": sum(o.steps_taken for o in outcomes) / len(outcomes),
        "avg_tokens": sum(o.tokens_used for o in outcomes) / len(outcomes),
        "avg_time_seconds": sum(o.time_elapsed_seconds for o in outcomes) / len(outcomes),
        "avg_tool_calls": sum(o.tool_calls_count for o in outcomes) / len(outcomes),

        # Efficiency
        "token_efficiency": token_efficiency(outcomes),

        # Breakdowns
        "by_category": success_rate_by_category(outcomes, tasks),
        "by_difficulty": success_rate_by_difficulty(outcomes, tasks),

        # Error analysis
        "error_count": sum(1 for o in outcomes if o.error),
        "timeout_count": sum(1 for o in outcomes if o.error and "Timeout" in o.error),
    }
