"""
ReviewFlow - Manages Doer-Critic iteration loop for self-correction.

This flow coordinates between a Doer agent (e.g., Manus) and a Reviewer agent,
iterating until the output passes review or max iterations are reached.
"""

import asyncio
from typing import Dict, Union

from pydantic import Field

from app.agent.base import BaseAgent
from app.agent.reviewer import Reviewer
from app.flow.base import BaseFlow
from app.logger import logger
from app.schema import AgentState


class ReviewFlow(BaseFlow):
    """
    Flow for managing Doer-Critic self-correction loops.

    Coordinates iterations between a Doer agent and Reviewer agent until
    output passes review or max iterations are reached.
    """

    max_iterations: int = Field(default=3, description="Maximum Doer-Critic iterations")
    current_iteration: int = Field(default=0, description="Current iteration count")

    def __init__(
        self,
        agents: Union[BaseAgent, Dict[str, BaseAgent]],
        max_iterations: int = 3,
        **kwargs,
    ):
        """
        Initialize ReviewFlow with Doer and Reviewer agents.

        Args:
            agents: Dict with 'doer' and 'reviewer' keys, or single doer agent
            max_iterations: Maximum number of Doer-Critic iterations
        """
        # Handle agents dict before super().__init__
        if isinstance(agents, dict):
            if "doer" not in agents:
                raise ValueError("ReviewFlow requires 'doer' agent in agents dict")
            if "reviewer" not in agents:
                # Create default reviewer if not provided
                agents["reviewer"] = Reviewer()
        else:
            # Single agent provided, treat as doer and create reviewer
            agents = {"doer": agents, "reviewer": Reviewer()}

        super().__init__(agents, **kwargs)
        self.max_iterations = max_iterations

    async def execute(self, input_text: str) -> str:
        """Execute the flow with given input (BaseFlow interface)."""
        return await self.run(input_text)

    async def run(self, request: str) -> str:
        """
        Execute Doer-Critic iteration loop.

        Args:
            request: Initial user request/task

        Returns:
            Final output string after review iterations
        """
        logger.info(f"🔄 Starting ReviewFlow with max {self.max_iterations} iterations")

        doer = self.agents["doer"]
        reviewer = self.agents["reviewer"]

        last_output = ""
        feedback = ""

        for iteration in range(1, self.max_iterations + 1):
            self.current_iteration = iteration
            logger.info(f"📝 ReviewFlow iteration {iteration}/{self.max_iterations}")

            # Doer executes task (with feedback from previous iteration if any)
            if iteration == 1:
                doer_prompt = request
            else:
                doer_prompt = f"""
PREVIOUS ATTEMPT:
{last_output[:500]}...

REVIEWER FEEDBACK:
{feedback}

Please address the reviewer's concerns and improve your solution.
"""

            logger.info(f"🛠️ Doer working on task...")
            doer_result = await doer.run(doer_prompt)
            last_output = doer_result

            # Reviewer evaluates the output
            review_prompt = f"""
Please review the following output:

TASK: {request[:200]}...

OUTPUT TO REVIEW:
{doer_result[:1000]}...

Provide your assessment.
"""

            logger.info(f"🔍 Reviewer evaluating output...")
            reviewer.state = AgentState.IDLE  # Reset reviewer state
            reviewer.current_step = 0
            review_result = await reviewer.run(review_prompt)

            # Extract grade
            grade = reviewer.extract_grade(review_result)
            logger.info(f"📊 Review grade: {grade}")

            if grade == "PASS":
                logger.info(f"✅ Output passed review on iteration {iteration}")
                return f"""FINAL OUTPUT (Passed review after {iteration} iteration(s)):

{doer_result}

---
REVIEWER'S ASSESSMENT:
{review_result}
"""
            else:
                logger.warning(f"❌ Output failed review on iteration {iteration}")
                feedback = review_result

                if iteration == self.max_iterations:
                    logger.warning(
                        f"⚠️ Max iterations ({self.max_iterations}) reached without passing review"
                    )
                    return f"""FINAL OUTPUT (Max iterations reached, did not pass review):

{doer_result}

---
LAST REVIEW:
{review_result}
"""

        # Should not reach here, but handle defensively
        return last_output
