#!/usr/bin/env python3
"""
Evaluation runner for OpenManus agent benchmarks.

Usage:
    python eval_runner.py --tasks eval/tasks --output eval/results
    python eval_runner.py --tasks eval/tasks/coding --categories coding
    python eval_runner.py --help

Runs evaluation tasks against the Manus agent and generates metrics reports.
"""

import asyncio
import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import List, Optional

from app.agent.manus import Manus
from app.eval.task import EvalTask
from app.eval.trial import TrialRunner
from app.eval.grader import CodeGrader, ModelGrader
from app.eval.metrics import aggregate_metrics


def load_tasks(tasks_dir: str) -> List[EvalTask]:
    """Load evaluation tasks from JSON files.

    Args:
        tasks_dir: Directory containing task JSON files

    Returns:
        List of EvalTask objects
    """
    tasks = []
    tasks_path = Path(tasks_dir)

    if not tasks_path.exists():
        print(f"Warning: Tasks directory not found: {tasks_dir}")
        return tasks

    for json_file in tasks_path.rglob("*.json"):
        try:
            with open(json_file, encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    tasks.extend(EvalTask(**t) for t in data)
                else:
                    tasks.append(EvalTask(**data))
            print(f"  Loaded: {json_file.name}")
        except Exception as e:
            print(f"  Error loading {json_file}: {e}")

    return tasks


async def run_evaluation(
    tasks_dir: str,
    output_dir: str,
    categories: Optional[List[str]] = None,
    difficulties: Optional[List[str]] = None,
    max_tasks: Optional[int] = None,
    verbose: bool = False
):
    """Run full evaluation suite.

    Args:
        tasks_dir: Directory containing task JSON files
        output_dir: Directory for results output
        categories: Optional list of categories to filter
        difficulties: Optional list of difficulties to filter
        max_tasks: Optional maximum number of tasks to run
        verbose: Print detailed output
    """
    print("=" * 60)
    print("OpenManus Evaluation Runner")
    print("=" * 60)
    print()

    # Load tasks
    print(f"Loading tasks from: {tasks_dir}")
    tasks = load_tasks(tasks_dir)

    if not tasks:
        print("No tasks found. Exiting.")
        return

    # Filter by category
    if categories:
        tasks = [t for t in tasks if t.category in categories]
        print(f"Filtered to categories: {categories}")

    # Filter by difficulty
    if difficulties:
        tasks = [t for t in tasks if t.difficulty in difficulties]
        print(f"Filtered to difficulties: {difficulties}")

    # Limit number of tasks
    if max_tasks and len(tasks) > max_tasks:
        tasks = tasks[:max_tasks]
        print(f"Limited to first {max_tasks} tasks")

    print(f"\nLoaded {len(tasks)} evaluation tasks")
    print()

    # Initialize graders
    # We'll create the ModelGrader with the agent's LLM later
    code_grader = CodeGrader()

    # Run trials
    outcomes = []
    errors = []

    for i, task in enumerate(tasks):
        print(f"[{i+1}/{len(tasks)}] Running: {task.task_id}")
        if verbose:
            print(f"        Category: {task.category}, Difficulty: {task.difficulty}")
            print(f"        Prompt: {task.prompt[:100]}...")

        try:
            # Create fresh agent for each task
            agent = await Manus.create()

            # Set up runner with graders
            graders = [code_grader]
            if task.grading_criteria:
                graders.append(ModelGrader(llm=agent.llm))

            runner = TrialRunner(graders=graders)
            outcome = await runner.run_trial(task, agent)
            outcomes.append(outcome)

            # Print result
            status = "PASS" if outcome.passed else "FAIL"
            status_color = "\033[92m" if outcome.passed else "\033[91m"
            reset_color = "\033[0m"

            print(f"        {status_color}{status}{reset_color} "
                  f"(score: {outcome.final_score:.2f}, "
                  f"tokens: {outcome.tokens_used}, "
                  f"steps: {outcome.steps_taken})")

            if outcome.error:
                print(f"        Error: {outcome.error[:100]}")

            # Cleanup agent
            await agent.cleanup()

        except Exception as e:
            print(f"        ERROR: {str(e)[:100]}")
            errors.append({"task_id": task.task_id, "error": str(e)})

    print()
    print("=" * 60)
    print("Results Summary")
    print("=" * 60)

    # Generate report
    task_map = {t.task_id: t for t in tasks}
    metrics = aggregate_metrics(outcomes, task_map)

    # Print summary
    print(f"\nTotal Tasks:    {metrics.get('total_trials', 0)}")
    print(f"Passed:         {metrics.get('passed', 0)}")
    print(f"Failed:         {metrics.get('failed', 0)}")
    print(f"Errors:         {len(errors)}")
    print()
    print(f"Pass Rate:      {metrics.get('pass_rate', 0):.1%}")
    print(f"Pass@1:         {metrics.get('pass_at_1', 0):.1%}")
    print(f"Pass@3:         {metrics.get('pass_at_3', 0):.1%}")
    print()
    print(f"Avg Score:      {metrics.get('avg_score', 0):.2f}")
    print(f"Avg Steps:      {metrics.get('avg_steps', 0):.1f}")
    print(f"Avg Tokens:     {metrics.get('avg_tokens', 0):.0f}")
    print(f"Avg Time:       {metrics.get('avg_time_seconds', 0):.1f}s")

    if metrics.get("by_category"):
        print("\nBy Category:")
        for cat, rate in metrics["by_category"].items():
            print(f"  {cat}: {rate:.1%}")

    if metrics.get("by_difficulty"):
        print("\nBy Difficulty:")
        for diff, rate in metrics["by_difficulty"].items():
            print(f"  {diff}: {rate:.1%}")

    # Save results
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = output_path / f"eval_results_{timestamp}.json"

    results = {
        "timestamp": timestamp,
        "tasks_dir": tasks_dir,
        "task_count": len(tasks),
        "metrics": metrics,
        "outcomes": [o.model_dump() for o in outcomes],
        "errors": errors
    }

    with open(results_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, default=str)

    print(f"\nResults saved to: {results_file}")


def main():
    parser = argparse.ArgumentParser(
        description="Run OpenManus evaluation suite",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python eval_runner.py
  python eval_runner.py --tasks eval/tasks/coding
  python eval_runner.py --categories coding reasoning
  python eval_runner.py --difficulties easy medium
  python eval_runner.py --max-tasks 10 --verbose
        """
    )
    parser.add_argument(
        "--tasks",
        default="eval/tasks",
        help="Path to tasks directory (default: eval/tasks)"
    )
    parser.add_argument(
        "--output",
        default="eval/results",
        help="Output directory for results (default: eval/results)"
    )
    parser.add_argument(
        "--categories",
        nargs="+",
        help="Filter by categories (e.g., coding tool_use reasoning)"
    )
    parser.add_argument(
        "--difficulties",
        nargs="+",
        help="Filter by difficulties (e.g., easy medium hard)"
    )
    parser.add_argument(
        "--max-tasks",
        type=int,
        help="Maximum number of tasks to run"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Print detailed output"
    )

    args = parser.parse_args()

    asyncio.run(run_evaluation(
        args.tasks,
        args.output,
        args.categories,
        args.difficulties,
        args.max_tasks,
        args.verbose
    ))


if __name__ == "__main__":
    main()
