"""
Trial outcome and grading result models for evaluation.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class GradeResult(BaseModel):
    """Result from a single grader."""

    passed: bool = Field(..., description="Whether the task passed this grader's criteria")
    score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Score between 0.0 and 1.0"
    )
    grader_type: str = Field(
        ...,
        description="Type of grader: code, model, or human"
    )
    reason: Optional[str] = Field(
        default=None,
        description="Explanation for the grade"
    )
    details: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional grading details"
    )


class TrialOutcome(BaseModel):
    """Complete outcome of a single evaluation trial run."""

    # Identifiers
    task_id: str = Field(..., description="ID of the task being evaluated")
    trial_id: str = Field(..., description="Unique ID for this trial run")
    run_timestamp: datetime = Field(
        default_factory=datetime.now,
        description="When the trial was executed"
    )

    # Execution results
    success: bool = Field(
        ...,
        description="Whether the agent completed without errors"
    )
    final_output: Optional[str] = Field(
        default=None,
        description="Final output from the agent"
    )
    error: Optional[str] = Field(
        default=None,
        description="Error message if execution failed"
    )

    # Grading
    grades: List[GradeResult] = Field(
        default_factory=list,
        description="Results from all graders"
    )
    final_score: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Aggregate score from all graders"
    )
    passed: bool = Field(
        default=False,
        description="Whether the task passed all graders"
    )

    # Performance metrics
    steps_taken: int = Field(
        default=0,
        description="Number of agent steps executed"
    )
    tokens_used: int = Field(
        default=0,
        description="Total tokens used (input + output)"
    )
    input_tokens: int = Field(
        default=0,
        description="Input tokens consumed"
    )
    output_tokens: int = Field(
        default=0,
        description="Output tokens generated"
    )
    time_elapsed_seconds: float = Field(
        default=0.0,
        description="Wall clock time in seconds"
    )
    tool_calls_count: int = Field(
        default=0,
        description="Number of tool calls made"
    )

    # Full transcript for debugging
    transcript: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Full message history from the trial"
    )

    class Config:
        extra = "allow"
