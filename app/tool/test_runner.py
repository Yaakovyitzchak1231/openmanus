"""
Test Runner Tool - Automated pytest/unittest execution for code validation.

This tool allows agents (especially the Reviewer) to programmatically run tests
to verify code quality and functionality.
"""

import subprocess
import sys
from typing import List, Optional

from app.logger import logger
from app.tool.base import BaseTool, ToolResult


class TestRunner(BaseTool):
    """A tool for executing pytest programmatically with configurable options."""

    name: str = "test_runner"
    description: str = (
        "Runs pytest on Python test files or directories. "
        "Use this to validate code functionality by executing unit tests. "
        "Returns test results including pass/fail status and detailed output."
    )
    parameters: dict = {
        "type": "object",
        "properties": {
            "test_path": {
                "type": "string",
                "description": "Path to test file or directory to run (relative or absolute)",
            },
            "test_args": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Optional pytest arguments (e.g., ['-v', '-k', 'test_name'])",
                "default": [],
            },
        },
        "required": ["test_path"],
    }

    async def execute(
        self,
        test_path: str,
        test_args: Optional[List[str]] = None,
        timeout: int = 120,  # Increased for longer test suites
    ) -> ToolResult:
        """
        Execute pytest on the specified test path.

        Args:
            test_path: Path to test file or directory
            test_args: Additional pytest arguments (default: ['-v'])
            timeout: Execution timeout in seconds (default: 120)

        Returns:
            ToolResult with test output and success status
        """
        if test_args is None:
            test_args = ["-v"]  # Verbose output by default

        # Build pytest command
        cmd = [sys.executable, "-m", "pytest", test_path] + test_args

        logger.info(f"Running pytest: {' '.join(cmd)}")

        try:
            # Run pytest as subprocess
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
            )

            # Format output
            output_lines = []
            output_lines.append(f"Command: {' '.join(cmd)}")
            output_lines.append(f"Exit Code: {result.returncode}")
            output_lines.append("\n=== STDOUT ===")
            output_lines.append(result.stdout)

            if result.stderr:
                output_lines.append("\n=== STDERR ===")
                output_lines.append(result.stderr)

            # Determine success (pytest exit code 0 = all tests passed)
            success = result.returncode == 0

            output_text = "\n".join(output_lines)

            if success:
                logger.info(f"Tests passed: {test_path}")
                return self.success_response(f"✅ All tests passed!\n\n{output_text}")
            else:
                logger.warning(
                    f"Tests failed: {test_path} (exit code {result.returncode})"
                )
                return ToolResult(
                    output=f"❌ Tests failed (exit code {result.returncode})\n\n{output_text}",
                    error=None,  # Not a tool error, just failed tests
                )

        except subprocess.TimeoutExpired:
            error_msg = f"Test execution timed out after {timeout} seconds"
            logger.error(error_msg)
            return self.fail_response(error_msg)

        except FileNotFoundError:
            error_msg = f"Test path not found: {test_path}"
            logger.error(error_msg)
            return self.fail_response(error_msg)

        except Exception as e:
            error_msg = f"Test execution failed: {str(e)}"
            logger.error(error_msg)
            return self.fail_response(error_msg)
