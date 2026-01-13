"""
Trial execution for evaluation tasks.

Runs an agent against an evaluation task and collects metrics.
"""

import asyncio
import uuid
from typing import List, Optional, TYPE_CHECKING
from datetime import datetime
from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from app.agent.base import BaseAgent
    from app.eval.task import EvalTask
    from app.eval.outcome import TrialOutcome
    from app.eval.grader import BaseGrader


class TrialRunner(BaseModel):
    """Runs evaluation trials and collects outcomes.

    Usage:
        runner = TrialRunner(graders=[CodeGrader(), ModelGrader(llm=llm)])
        outcome = await runner.run_trial(task, agent)
    """

    graders: List["BaseGrader"] = Field(
        default_factory=list,
        description="List of graders to apply to outcomes"
    )

    class Config:
        arbitrary_types_allowed = True

    async def run_trial(
        self,
        task: "EvalTask",
        agent: "BaseAgent"
    ) -> "TrialOutcome":
        """Execute a single trial and grade the result.

        Args:
            task: The evaluation task to run
            agent: The agent instance to evaluate

        Returns:
            TrialOutcome with execution results and grades
        """
        from app.eval.outcome import TrialOutcome

        trial_id = str(uuid.uuid4())[:8]
        start_time = datetime.now()

        # Configure agent for task
        agent.max_steps = task.max_steps
        if hasattr(agent, 'effort_level'):
            agent.effort_level = task.effort_level

        try:
            # Run agent with timeout
            result = await asyncio.wait_for(
                agent.run(task.prompt),
                timeout=task.timeout_seconds
            )

            # Collect metrics
            elapsed = (datetime.now() - start_time).total_seconds()

            # Get token counts from LLM if available
            input_tokens = getattr(agent.llm, "total_input_tokens", 0)
            output_tokens = getattr(agent.llm, "total_output_tokens", 0)
            tokens = input_tokens + output_tokens

            # Get final assistant message as output
            final_output = None
            for msg in reversed(agent.memory.messages):
                if msg.role == "assistant" and msg.content:
                    final_output = msg.content
                    break

            # Count tool calls
            tool_calls_count = sum(
                1 for m in agent.memory.messages
                if m.tool_calls
            )

            # Create outcome
            outcome = TrialOutcome(
                task_id=task.task_id,
                trial_id=trial_id,
                success=True,
                final_output=final_output,
                steps_taken=agent.current_step,
                tokens_used=tokens,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                time_elapsed_seconds=elapsed,
                tool_calls_count=tool_calls_count,
                transcript=[m.to_dict() for m in agent.memory.messages]
            )

            # Apply all graders
            grades = []
            for grader in self.graders:
                try:
                    grade = await grader.grade(task, outcome)
                    grades.append(grade)
                except Exception as e:
                    from app.eval.outcome import GradeResult
                    grades.append(GradeResult(
                        passed=False,
                        score=0.0,
                        grader_type=grader.name,
                        reason=f"Grader error: {str(e)}"
                    ))

            outcome.grades = grades

            # Calculate final score and pass status
            if grades:
                outcome.final_score = sum(g.score for g in grades) / len(grades)
                outcome.passed = all(g.passed for g in grades)

            return outcome

        except asyncio.TimeoutError:
            elapsed = (datetime.now() - start_time).total_seconds()
            return TrialOutcome(
                task_id=task.task_id,
                trial_id=trial_id,
                success=False,
                error=f"Timeout after {task.timeout_seconds}s",
                time_elapsed_seconds=elapsed
            )
        except Exception as e:
            elapsed = (datetime.now() - start_time).total_seconds()
            return TrialOutcome(
                task_id=task.task_id,
                trial_id=trial_id,
                success=False,
                error=str(e),
                time_elapsed_seconds=elapsed
            )

    async def run_multiple_trials(
        self,
        task: "EvalTask",
        agent_factory,
        n: int = 1
    ) -> List["TrialOutcome"]:
        """Run multiple trials of the same task.

        Args:
            task: The evaluation task to run
            agent_factory: Callable that creates a fresh agent instance
            n: Number of trials to run

        Returns:
            List of TrialOutcome objects
        """
        outcomes = []
        for _ in range(n):
            agent = await agent_factory()
            outcome = await self.run_trial(task, agent)
            outcomes.append(outcome)
        return outcomes
