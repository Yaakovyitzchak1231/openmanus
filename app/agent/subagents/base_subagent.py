"""
Base Sub-Agent

Foundation class for all specialized sub-agents. Sub-agents inherit from BaseAgent
but have specialized prompts and tool configurations for specific tasks.
"""

from typing import Any, Dict, Optional

from pydantic import Field

from app.agent.base import BaseAgent
from app.logger import logger


class BaseSubAgent(BaseAgent):
    """
    Base class for all specialized sub-agents.

    Sub-agents are spawned by the main orchestrator via the Task tool to handle
    specific types of tasks (exploration, planning, coding, testing, etc.).

    Each sub-agent has:
    - Specialized system prompt for its purpose
    - Optimized tool set for its capabilities
    - Configured max_steps appropriate for its task
    - Task-specific configuration
    """

    # Sub-agent configuration
    agent_type: str = Field(
        ..., description="Type of sub-agent (explore, plan, code, etc.)"
    )
    task_description: str = Field(
        ..., description="Task the sub-agent should accomplish"
    )
    task_context: Dict[str, Any] = Field(
        default_factory=dict, description="Additional context for the task"
    )

    # Override defaults with sub-agent specific values
    max_steps: int = Field(default=20, description="Maximum steps for this sub-agent")

    def __init__(self, **data):
        """Initialize sub-agent with task-specific configuration"""
        super().__init__(**data)
        logger.info(f"🤖 Initialized {self.agent_type} sub-agent: {self.name}")

    async def run(self, request: Optional[str] = None) -> str:
        """
        Run the sub-agent on its assigned task.

        The request parameter is optional because sub-agents are initialized with
        their task_description, which is used as the initial user message.

        Returns:
            Summary of the sub-agent's work and findings
        """
        # Use task_description as the initial request if no explicit request given
        initial_request = request or self.task_description

        logger.info(f"▶️  Starting {self.agent_type} sub-agent execution")
        logger.info(f"📋 Task: {initial_request[:100]}...")

        # Run the base agent execution
        result = await super().run(initial_request)

        logger.info(f"✅ {self.agent_type} sub-agent completed")

        return result

    def _get_initial_context_message(self) -> str:
        """
        Generate an initial context message for the sub-agent.

        This provides the sub-agent with information about its task context,
        any files to focus on, previous results, constraints, etc.
        """
        if not self.task_context:
            return ""

        context_parts = []

        if "files" in self.task_context:
            files = self.task_context["files"]
            context_parts.append(f"Focus on these files: {', '.join(files)}")

        if "previous_results" in self.task_context:
            context_parts.append(
                f"Previous results:\n{self.task_context['previous_results']}"
            )

        if "constraints" in self.task_context:
            constraints = self.task_context["constraints"]
            if isinstance(constraints, list):
                context_parts.append(f"Constraints: {', '.join(constraints)}")
            else:
                context_parts.append(f"Constraints: {constraints}")

        if "mode" in self.task_context:
            context_parts.append(f"Mode: {self.task_context['mode']}")

        return "\n\n".join(context_parts) if context_parts else ""

    @classmethod
    def create_for_task(
        cls, task: str, context: Optional[Dict[str, Any]] = None, **kwargs
    ) -> "BaseSubAgent":
        """
        Factory method to create a sub-agent for a specific task.

        Args:
            task: Task description
            context: Optional context dictionary
            **kwargs: Additional configuration

        Returns:
            Configured sub-agent instance
        """
        return cls(task_description=task, task_context=context or {}, **kwargs)
