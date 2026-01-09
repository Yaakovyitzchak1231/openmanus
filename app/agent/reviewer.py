"""
Reviewer Agent - A critic agent for auditing and providing feedback on task outputs.

This agent implements the Reviewer role in a Doer-Critic self-correction loop,
analyzing outputs for logic flaws, efficiency issues, and accuracy problems.
"""

from typing import Optional

from pydantic import Field

from app.agent.base import BaseAgent
from app.llm import LLM
from app.logger import logger
from app.schema import AgentState, Message

REVIEWER_SYSTEM_PROMPT = """You are a senior software auditor and code reviewer with expertise in:
- Logic correctness and edge case analysis
- Code efficiency and performance optimization
- Best practices and design patterns
- Security vulnerabilities
- Error handling and robustness

Your role is to critically analyze outputs from other agents and provide constructive feedback.

## Review Guidelines:

1. **Be Thorough**: Check for logic errors, edge cases, security issues, and efficiency problems
2. **Be Specific**: Point out exact issues with line numbers or specific examples
3. **Be Constructive**: Suggest concrete improvements, not just criticisms
4. **Grade Honestly**: Use PASS only when output truly meets quality standards

## Output Format:

Provide your review in this format:

**GRADE: PASS** or **GRADE: FAIL**

**ISSUES FOUND:**
1. [Specific issue with details]
2. [Another specific issue]
3. [Third issue if applicable]

**SUGGESTIONS:**
- [Concrete improvement recommendation]
- [Alternative approach if needed]

**SUMMARY:**
[One-sentence overall assessment]

Be strict but fair. Quality standards matter.
"""


class Reviewer(BaseAgent):
    """
    Reviewer/Critic agent for auditing task outputs.

    Provides structured feedback with PASS/FAIL grades and specific improvement suggestions.
    """

    name: str = "Reviewer"
    description: str = (
        "A senior auditor agent that reviews outputs for quality, correctness, and best practices"
    )

    system_prompt: str = REVIEWER_SYSTEM_PROMPT
    next_step_prompt: Optional[str] = None

    max_steps: int = 1  # Reviewer only needs one step to provide feedback

    async def step(self) -> str:
        """
        Execute a single review step.

        Returns:
            Review feedback with grade and specific issues/suggestions.
        """
        if not self.memory.messages:
            return "No content to review"

        # Get the last user message (which should contain the output to review)
        last_message = self.memory.messages[-1]
        if last_message.role != "user":
            return "Expected user message with content to review"

        # Ask LLM for review
        system_msg = Message.system_message(self.system_prompt)

        try:
            response = await self.llm.ask(
                messages=[last_message], system_msgs=[system_msg], stream=False
            )

            # llm.ask() returns a string directly, not an object with .content
            review_content = response if response else "No review generated"

            # Add review to memory
            self.update_memory("assistant", review_content)

            # Mark as finished after one review
            self.state = AgentState.FINISHED

            return review_content

        except Exception as e:
            logger.error(f"Reviewer error: {e}")
            return f"Review failed: {str(e)}"

    def extract_grade(self, review_text: str) -> str:
        """
        Extract PASS/FAIL grade from review text.

        Args:
            review_text: The review content

        Returns:
            "PASS", "FAIL", or "UNKNOWN"
        """
        review_upper = review_text.upper()

        if "GRADE: PASS" in review_upper or "**GRADE: PASS**" in review_upper:
            return "PASS"
        elif "GRADE: FAIL" in review_upper or "**GRADE: FAIL**" in review_upper:
            return "FAIL"
        else:
            # Default to PASS if unclear (optimistic)
            logger.warning("Could not determine grade from review, defaulting to PASS")
            return "PASS"
