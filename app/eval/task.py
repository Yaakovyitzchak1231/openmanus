"""
Evaluation task definitions for agent benchmarking.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class EvalTask(BaseModel):
    """Defines an evaluation task (test case) for agent benchmarking."""

    task_id: str = Field(..., description="Unique task identifier")
    prompt: str = Field(..., description="The task prompt/instruction for the agent")
    category: str = Field(
        default="general",
        description="Task category: coding, tool_use, reasoning, etc."
    )

    # Expected outcomes for grading
    expected_output: Optional[str] = Field(
        default=None,
        description="Expected output for exact match grading"
    )
    expected_patterns: List[str] = Field(
        default_factory=list,
        description="Regex patterns that should match in the output"
    )
    grading_criteria: List[str] = Field(
        default_factory=list,
        description="Criteria for model-based (LLM) grading"
    )

    # Test execution for code tasks
    test_code: Optional[str] = Field(
        default=None,
        description="Python test code to verify solution. Must set 'test_result' variable."
    )
    test_file: Optional[str] = Field(
        default=None,
        description="Path to pytest file to execute for grading"
    )

    # Execution limits
    timeout_seconds: int = Field(
        default=300,
        description="Maximum execution time in seconds"
    )
    max_steps: int = Field(
        default=20,
        description="Maximum agent steps allowed"
    )
    effort_level: str = Field(
        default="medium",
        description="Agent effort level: low, medium, high"
    )

    # Metadata
    difficulty: str = Field(
        default="medium",
        description="Task difficulty: easy, medium, hard"
    )
    tags: List[str] = Field(
        default_factory=list,
        description="Tags for categorization and filtering"
    )

    class Config:
        extra = "allow"  # Allow additional fields for extensibility
