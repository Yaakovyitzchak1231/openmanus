"""
Reviewer Agent - A critic agent for auditing and providing feedback on task outputs.

This agent implements the Reviewer role in a Doer-Critic self-correction loop,
analyzing outputs for logic flaws, efficiency issues, and accuracy problems.
"""

import re
from pathlib import Path
from typing import Optional

from pydantic import Field

from app.agent.toolcall import ToolCallAgent
from app.logger import logger
from app.tool import ToolCollection
from app.tool.test_runner import TestRunner


REVIEWER_SYSTEM_PROMPT = """You are a senior software auditor and code reviewer with expertise in:
- Logic correctness and edge case analysis
- Code efficiency and performance optimization
- Best practices and design patterns
- Security vulnerabilities
- Error handling and robustness

Your role is to critically analyze outputs from other agents and provide constructive feedback.

## Chain-of-Thought Review Process

**BEFORE grading, systematically analyze using these questions:**

### 1. Logic & Correctness
- Does the code/solution actually solve the stated problem?
- Are there any logical errors or flaws in the approach?
- What happens with edge cases: empty inputs, null values, extremely large inputs?
- Are array indices within bounds? Do loops terminate correctly?

### 2. Error Handling & Robustness
- What can go wrong? (file not found, network errors, invalid input types)
- Are errors caught and handled gracefully?
- Are error messages helpful for debugging?
- Does the code fail safely or cause cascading failures?

### 3. Quality & Best Practices
- Is the code readable with clear variable names?
- Are there proper comments/docstrings?
- Does it follow language conventions?
- Is the approach efficient or unnecessarily complex?

### 4. Security & Safety
- Any injection vulnerabilities (SQL, command, etc.)?
- Is user input validated and sanitized?
- Are credentials or sensitive data exposed?
- Are permissions/access controls appropriate?

### 5. Testing & Verification
- Are there tests? Do they cover edge cases?
- Can the solution be easily tested?
- Is there evidence the code was actually run and verified?
- **If reviewing Python code with tests, use the test_runner tool to execute tests and validate functionality**

## Grading Standard

**PASS**: Code meets professional standards, handles edge cases, has error handling, and is production-ready (or close)

**FAIL**: Code has logic errors, missing error handling, security issues, or fails basic test cases

## Output Format

**THINK STEP-BY-STEP** (show your analysis):
[Walk through your reasoning using the framework above]

**GRADE: PASS** or **GRADE: FAIL**

**ISSUES FOUND:**
1. [Specific issue with details - cite line numbers or examples]
2. [Another specific issue]
3. [Third issue if applicable]

**SUGGESTIONS:**
- [Concrete improvement recommendation]
- [Alternative approach if needed]

**SUMMARY:**
[One-sentence overall assessment]

Be strict but fair. Thoughtful analysis produces better feedback.
"""


class Reviewer(ToolCallAgent):
    """
    Reviewer/Critic agent for auditing task outputs.

    Provides structured feedback with PASS/FAIL grades and specific improvement suggestions.
    Can use the test_runner tool to validate code with tests.
    """

    name: str = "Reviewer"
    description: str = (
        "A senior auditor agent that reviews outputs for quality, correctness, and best practices. "
        "Can run tests to validate code functionality."
    )

    system_prompt: str = REVIEWER_SYSTEM_PROMPT
    next_step_prompt: Optional[str] = None

    max_steps: int = 3  # Allow up to 3 steps for: review, test, and final assessment

    # Add test_runner tool for code validation
    available_tools: ToolCollection = Field(
        default_factory=lambda: ToolCollection(
            TestRunner(),
        )
    )

    async def step(self) -> str:
        """
        Execute a single review step with optional test execution.

        Auto-detects Python code files and runs tests when appropriate.

        Returns:
            Review feedback with grade and specific issues/suggestions.
        """
        if not self.memory.messages:
            return "No content to review"

        # Get the last user message (which should contain the output to review)
        last_message = self.memory.messages[-1]
        if last_message.role != "user":
            return "Expected user message with content to review"

        content_to_review = last_message.content

        # Auto-detect if we should run tests
        test_file_path = self._detect_test_file(content_to_review)

        if test_file_path and self.current_step == 0:
            # First step: Run tests if test file detected
            logger.info(f"Auto-detected test file: {test_file_path}. Running tests...")

            try:
                test_runner = TestRunner()
                test_result = await test_runner.execute(
                    test_path=test_file_path, test_args=["-v"]
                )

                # Add test results to review context
                test_context = f"\n\n## Automated Test Results\n\n{test_result.output or test_result.error}\n"
                enhanced_content = content_to_review + test_context

                # Update memory with test results
                self.update_memory("user", enhanced_content)

                return f"✅ Tests executed. Proceeding with review incorporating test results."

            except Exception as e:
                logger.error(f"Failed to run tests: {e}")
                # Continue with review even if tests fail

        # Use parent class think() for tool-based reasoning
        return await super().step()

    def _detect_test_file(self, content: str) -> Optional[str]:
        """
        Detect if content references a test file that can be executed.

        Args:
            content: The content to review

        Returns:
            Path to test file if detected, None otherwise
        """
        # Look for common test file patterns
        test_patterns = [
            r"test_[\w]+\.py",  # test_filename.py
            r"[\w]+_test\.py",  # filename_test.py
            r"tests/[\w/]+\.py",  # tests/path/to/file.py
        ]

        for pattern in test_patterns:
            matches = re.findall(pattern, content)
            if matches:
                # Take the first match
                potential_path = matches[0]

                # Verify file exists
                if Path(potential_path).exists():
                    return potential_path

                # Try common test directories
                for test_dir in ["tests", "test", "."]:
                    full_path = Path(test_dir) / potential_path
                    if full_path.exists():
                        return str(full_path)

        return None

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
