"""
Test Agent

Automated testing and validation. Specialized in running pytest, validating functionality,
and checking test coverage.
"""

from pydantic import Field

from app.agent.subagents.base_subagent import BaseSubAgent
from app.tool import Terminate
from app.tool.bash import Bash
from app.tool.python_execute import PythonExecute
from app.tool.test_runner import TestRunner
from app.tool.tool_collection import ToolCollection


TEST_SYSTEM_PROMPT = """You are a Test Agent specialized in automated testing and validation.

Your capabilities:
- Run pytest and unittest test suites
- Execute individual tests or test files
- Validate functionality end-to-end
- Check test coverage
- Identify failing tests and analyze errors
- Run integration and unit tests

Your approach:
1. **Discover**: Find all test files (test_*.py, *_test.py)
2. **Run**: Execute tests using pytest or unittest
3. **Analyze**: Review test output, identify failures
4. **Report**: Provide clear summary of results
5. **Debug**: For failures, analyze error messages and suggest fixes

Test Execution Options:
- Run all tests: pytest
- Run specific file: pytest path/to/test_file.py
- Run specific test: pytest path/to/test_file.py::test_function
- With coverage: pytest --cov=app --cov-report=term-missing
- Verbose mode: pytest -v

When complete, use the Terminate tool with a summary of:
- Total tests run
- Passed / Failed / Skipped
- Test coverage percentage (if available)
- Any critical failures or issues"""

TEST_NEXT_STEP_PROMPT = """Continue testing and validation.

Remember to:
- Run all relevant tests
- Check for test failures
- Analyze error messages
- Report coverage if possible
- Use Terminate when testing is complete"""


class TestAgent(BaseSubAgent):
    """
    Test Agent for automated testing and validation.

    Optimized for:
    - Running pytest and unittest
    - Test discovery and execution
    - Coverage analysis
    - Failure diagnosis

    Configured for thorough testing with moderate steps.
    """

    name: str = "test_agent"
    description: str = "Automated testing and validation specialist"
    agent_type: str = "test"

    # Configuration for testing
    max_steps: int = Field(default=15, description="Moderate steps for test execution")
    effort_level: str = Field(default="normal", description="Normal effort for testing")

    # Specialized prompts
    system_prompt: str = TEST_SYSTEM_PROMPT
    next_step_prompt: str = TEST_NEXT_STEP_PROMPT

    # Tool set for testing
    available_tools: ToolCollection = Field(
        default_factory=lambda: ToolCollection(
            Bash(),  # For pytest commands, test discovery
            PythonExecute(),  # For running Python tests directly
            TestRunner(),  # Specialized test runner tool
            Terminate(),  # To signal completion
        )
    )

    def __init__(self, **data):
        """Initialize Test Agent with testing configuration"""
        data.setdefault("name", "test_agent")
        data.setdefault("agent_type", "test")
        super().__init__(**data)
