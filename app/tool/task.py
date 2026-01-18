"""
Task Tool - Spawn specialized sub-agents to handle complex tasks

This implements the Claude Opus 4.5 Task orchestration pattern where a main agent
can spawn specialized sub-agents (Explore, Plan, Code, Test, Build, Review) for
specific capabilities.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any, Dict, Optional

from pydantic import Field

from app.logger import logger
from app.tool.base import BaseTool, ToolResult


if TYPE_CHECKING:
    from app.harness.subagent_registry import SubAgentRegistry


class TaskTool(BaseTool):
    """
    Spawn specialized sub-agents to handle complex, multi-step tasks.

    This mirrors Claude Code CLI's Task tool pattern where the main orchestrator
    can delegate to specialized agents:
    - Explore: Fast codebase search and understanding
    - Plan: Implementation design and architecture planning
    - Code: Long-running coding with Initializer/Coding patterns
    - Test: Automated testing and validation
    - Build: Build verification and error checking
    - Review: Code review and quality assessment
    """

    name: str = "task"
    description: str = (
        "Spawn a specialized sub-agent to handle complex tasks autonomously. "
        "Each sub-agent has specific capabilities and can work independently. "
        "Use this when you need deep exploration, detailed planning, long-running "
        "coding sessions, comprehensive testing, build validation, or code review. "
        "The sub-agent will return its results when complete."
    )
    parameters: dict = {
        "type": "object",
        "properties": {
            "agent_type": {
                "type": "string",
                "enum": ["explore", "plan", "code", "test", "build", "review"],
                "description": (
                    "Type of sub-agent to spawn:\n"
                    "- explore: Fast codebase search, file discovery, pattern finding\n"
                    "- plan: Architecture design, implementation strategy, trade-off analysis\n"
                    "- code: Long-running coding with session management (init.sh, feature tracking)\n"
                    "- test: Run pytest, validate functionality, check test coverage\n"
                    "- build: Verify build process, check dependencies, validate setup\n"
                    "- review: Code quality assessment, security analysis, best practices check"
                ),
            },
            "task": {
                "type": "string",
                "description": (
                    "Detailed task description for the sub-agent. Be specific about "
                    "what you want the agent to accomplish. For 'code' agent, include "
                    "project requirements and features needed."
                ),
            },
            "context": {
                "type": "object",
                "description": (
                    "Optional context to pass to the sub-agent. Can include:\n"
                    "- files: List of file paths to focus on\n"
                    "- previous_results: Results from other sub-agents\n"
                    "- constraints: Limitations or requirements\n"
                    "- mode: For 'code' agent, specify 'initializer' or 'coding'"
                ),
            },
        },
        "required": ["agent_type", "task"],
    }

    # Registry will be injected at initialization
    subagent_registry: Optional[SubAgentRegistry] = Field(default=None, exclude=True)

    async def execute(
        self,
        agent_type: str,
        task: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> ToolResult:
        """
        Spawn a sub-agent and execute the task.

        Args:
            agent_type: Type of sub-agent (explore, plan, code, test, build, review)
            task: Detailed task description
            context: Optional context dict with files, results, constraints, mode

        Returns:
            ToolResult with sub-agent's output
        """
        if not self.subagent_registry:
            return self.fail_response(
                "SubAgent registry not initialized. This is a configuration error."
            )

        # Validate agent type
        if agent_type not in self.subagent_registry.agents:
            available = ", ".join(self.subagent_registry.agents.keys())
            return self.fail_response(
                f"Unknown agent type '{agent_type}'. Available: {available}"
            )

        logger.info(f"🚀 Spawning {agent_type} sub-agent for task: {task[:100]}...")

        try:
            # Spawn the sub-agent
            subagent = self.subagent_registry.spawn(
                agent_type=agent_type,
                task=task,
                context=context or {},
            )

            # Run the sub-agent
            logger.info(f"▶️  Running {agent_type} sub-agent...")
            result = await subagent.run()

            # Format result
            logger.info(f"✅ {agent_type} sub-agent completed successfully")

            output = {
                "agent_type": agent_type,
                "task": task,
                "result": result,
                "status": "completed",
                "steps_taken": getattr(subagent, "current_step", 0),
            }

            return ToolResult(
                output=json.dumps(output, indent=2, ensure_ascii=False),
                base64_image=None,
            )

        except Exception as e:
            logger.error(f"❌ {agent_type} sub-agent failed: {e}", exc_info=True)
            return self.fail_response(
                f"{agent_type} sub-agent failed: {str(e)}\n"
                f"Task was: {task[:200]}..."
            )

    def fail_response(self, message: str) -> ToolResult:
        """Helper to create failure responses"""
        return ToolResult(
            output=json.dumps(
                {"status": "error", "message": message}, indent=2, ensure_ascii=False
            ),
            base64_image=None,
        )
