"""
Grading implementations for evaluation tasks.

Supports three types of grading:
- CodeGrader: Regex matching, exact comparison, and code execution
- ModelGrader: LLM-based assessment with rubric
- (Future) HumanGrader: Manual review
"""

import re
import subprocess
from abc import ABC, abstractmethod
from typing import ClassVar, Optional, TYPE_CHECKING
from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from app.eval.task import EvalTask
    from app.eval.outcome import TrialOutcome, GradeResult
    from app.llm import LLM


class BaseGrader(ABC, BaseModel):
    """Base class for all graders."""

    name: str = Field(default="base", description="Grader name for identification")

    class Config:
        arbitrary_types_allowed = True

    @abstractmethod
    async def grade(self, task: "EvalTask", outcome: "TrialOutcome") -> "GradeResult":
        """Grade the outcome against the task criteria.

        Args:
            task: The evaluation task definition
            outcome: The trial execution outcome to grade

        Returns:
            GradeResult with pass/fail, score, and explanation
        """
        pass


class CodeGrader(BaseGrader):
    """Grade using code execution, regex matching, or exact comparison.

    Grading priority:
    1. Exact output match (if expected_output is set)
    2. Regex pattern matching (if expected_patterns is set)
    3. Test code execution (if test_code is set)
    4. Pytest file execution (if test_file is set)
    """

    name: str = "code"

    async def grade(self, task: "EvalTask", outcome: "TrialOutcome") -> "GradeResult":
        from app.eval.outcome import GradeResult

        # No output to grade
        if not outcome.final_output and not task.test_file and not task.test_code:
            return GradeResult(
                passed=False,
                score=0.0,
                grader_type="code",
                reason="No output to grade and no test specified"
            )

        # 1. Check exact match
        if task.expected_output and outcome.final_output:
            if task.expected_output.strip() == outcome.final_output.strip():
                return GradeResult(
                    passed=True,
                    score=1.0,
                    grader_type="code",
                    reason="Exact match"
                )

        # 2. Check regex patterns
        if task.expected_patterns and outcome.final_output:
            matches = sum(
                1 for p in task.expected_patterns
                if re.search(p, outcome.final_output, re.MULTILINE | re.DOTALL)
            )
            total = len(task.expected_patterns)
            score = matches / total if total > 0 else 0.0
            passed = score >= 0.8  # 80% threshold for pattern matching

            return GradeResult(
                passed=passed,
                score=score,
                grader_type="code",
                reason=f"Pattern match: {matches}/{total} patterns",
                details={"matches": matches, "total": total}
            )

        # 3. Run test code
        if task.test_code:
            try:
                exec_globals = {"output": outcome.final_output}
                exec(task.test_code, exec_globals)
                test_result = exec_globals.get("test_result", False)

                return GradeResult(
                    passed=bool(test_result),
                    score=1.0 if test_result else 0.0,
                    grader_type="code",
                    reason="Test code passed" if test_result else "Test code failed"
                )
            except Exception as e:
                return GradeResult(
                    passed=False,
                    score=0.0,
                    grader_type="code",
                    reason=f"Test execution error: {str(e)}"
                )

        # 4. Run pytest
        if task.test_file:
            try:
                result = subprocess.run(
                    ["pytest", task.test_file, "-v", "--tb=short"],
                    capture_output=True,
                    text=True,
                    timeout=60
                )
                passed = result.returncode == 0

                return GradeResult(
                    passed=passed,
                    score=1.0 if passed else 0.0,
                    grader_type="code",
                    reason=result.stdout[:500] if result.stdout else "No output",
                    details={"returncode": result.returncode}
                )
            except subprocess.TimeoutExpired:
                return GradeResult(
                    passed=False,
                    score=0.0,
                    grader_type="code",
                    reason="Pytest timeout (60s)"
                )
            except Exception as e:
                return GradeResult(
                    passed=False,
                    score=0.0,
                    grader_type="code",
                    reason=f"Pytest error: {str(e)}"
                )

        return GradeResult(
            passed=False,
            score=0.0,
            grader_type="code",
            reason="No grading criteria matched"
        )


class ModelGrader(BaseGrader):
    """Grade using LLM-based assessment with rubric.

    Uses the provided LLM to evaluate the agent's output against
    the task's grading_criteria.
    """

    name: str = "model"
    llm: Optional["LLM"] = None

    GRADING_PROMPT: ClassVar[str] = """You are evaluating an AI agent's response to a task.

Task: {prompt}

Grading Criteria:
{criteria}

Agent's Output:
{output}

Grade this response on a scale of 0.0 to 1.0 based on the criteria above.
Consider:
- Did the agent complete the task correctly?
- Did it follow all the specified criteria?
- Is the output well-formed and complete?

Respond in this EXACT format (one item per line):
SCORE: <number between 0.0 and 1.0>
PASSED: <true or false>
REASON: <brief 1-2 sentence explanation>"""

    async def grade(self, task: "EvalTask", outcome: "TrialOutcome") -> "GradeResult":
        from app.eval.outcome import GradeResult

        if not self.llm:
            return GradeResult(
                passed=False,
                score=0.0,
                grader_type="model",
                reason="No LLM configured for grading"
            )

        if not task.grading_criteria:
            return GradeResult(
                passed=False,
                score=0.0,
                grader_type="model",
                reason="No grading criteria specified"
            )

        criteria = "\n".join(f"- {c}" for c in task.grading_criteria)
        prompt = self.GRADING_PROMPT.format(
            prompt=task.prompt,
            criteria=criteria,
            output=outcome.final_output or "(no output)"
        )

        try:
            response = await self.llm.ask([{"role": "user", "content": prompt}])

            # Parse response
            score = 0.0
            passed = False
            reason = "Could not parse grading response"

            for line in response.split("\n"):
                line = line.strip()
                if line.upper().startswith("SCORE:"):
                    try:
                        score = float(line.split(":", 1)[1].strip())
                        score = max(0.0, min(1.0, score))  # Clamp to [0, 1]
                    except ValueError:
                        pass
                elif line.upper().startswith("PASSED:"):
                    passed = line.split(":", 1)[1].strip().lower() == "true"
                elif line.upper().startswith("REASON:"):
                    reason = line.split(":", 1)[1].strip()

            return GradeResult(
                passed=passed,
                score=score,
                grader_type="model",
                reason=reason
            )
        except Exception as e:
            return GradeResult(
                passed=False,
                score=0.0,
                grader_type="model",
                reason=f"Grading error: {str(e)}"
            )
