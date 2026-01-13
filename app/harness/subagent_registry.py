"""
Sub-Agent Registry

Central registry for all specialized sub-agents with routing logic to select
the best agent for a given task.
"""

from typing import Any, Dict, Optional, Type

from pydantic import BaseModel

from app.agent.reviewer import Reviewer  # Existing review agent
from app.agent.subagents.base_subagent import BaseSubAgent
from app.agent.subagents.build_agent import BuildAgent
from app.agent.subagents.coding_agent import CodingAgent
from app.agent.subagents.explore_agent import ExploreAgent
from app.agent.subagents.plan_agent import PlanAgent
from app.agent.subagents.test_agent import TestAgent
from app.config import Config
from app.llm import LLM
from app.logger import logger


class SubAgentRegistry(BaseModel):
    """
    Registry of available sub-agents with routing and spawning logic.

    This class maintains a mapping of agent types to their implementations
    and provides intelligent routing to select the best agent for a task.
    """

    # Registry of available sub-agents
    agents: Dict[str, Type[BaseSubAgent]] = {
        "explore": ExploreAgent,
        "plan": PlanAgent,
        "code": CodingAgent,
        "test": TestAgent,
        "build": BuildAgent,
        "review": Reviewer,  # Existing review agent
    }

    class Config:
        arbitrary_types_allowed = True

    def spawn(
        self,
        agent_type: str,
        task: str,
        context: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> BaseSubAgent:
        """
        Spawn a sub-agent instance configured for the given task.

        Args:
            agent_type: Type of agent to spawn (explore, plan, code, etc.)
            task: Task description
            context: Optional context dictionary
            **kwargs: Additional configuration for the agent

        Returns:
            Configured sub-agent instance

        Raises:
            ValueError: If agent_type is not registered
        """
        if agent_type not in self.agents:
            available = ", ".join(self.agents.keys())
            raise ValueError(
                f"Unknown agent type '{agent_type}'. Available: {available}"
            )

        agent_class = self.agents[agent_type]

        # Get configuration for this agent type from config
        config = Config()
        agent_config = self._get_agent_config(agent_type, config)

        # Merge with any provided kwargs
        agent_config.update(kwargs)

        # Create agent instance
        logger.info(f"🏗️  Spawning {agent_type} agent for task")

        agent = agent_class.create_for_task(task=task, context=context, **agent_config)

        return agent

    def _get_agent_config(self, agent_type: str, config: Config) -> Dict[str, Any]:
        """
        Get configuration for a specific agent type from global config.

        Args:
            agent_type: Type of agent
            config: Global configuration

        Returns:
            Configuration dict for the agent
        """
        # Base configuration
        agent_config = {
            "llm": LLM(),  # Create LLM instance for the agent
        }

        # Get agent-specific settings from config if available
        try:
            subagent_settings = config.get_setting("agent.subagents", {})

            # Get max_steps for this agent type
            max_steps_key = f"{agent_type}_max_steps"
            if max_steps_key in subagent_settings:
                agent_config["max_steps"] = subagent_settings[max_steps_key]

            # Get agent-specific settings (e.g., coding agent settings)
            agent_specific = subagent_settings.get(agent_type, {})
            agent_config.update(agent_specific)

        except Exception as e:
            logger.warning(
                f"Could not load config for {agent_type} agent: {e}. Using defaults."
            )

        return agent_config

    def route_task(self, task_description: str) -> str:
        """
        Automatically route a task to the best agent based on description.

        This analyzes the task description and selects the most appropriate
        agent type. Useful for auto-routing when agent_type is not specified.

        Args:
            task_description: Description of the task

        Returns:
            Best agent type for this task
        """
        task_lower = task_description.lower()

        # Keyword-based routing rules
        if any(
            kw in task_lower
            for kw in ["find", "search", "locate", "where is", "explore", "discover"]
        ):
            return "explore"

        if any(
            kw in task_lower
            for kw in [
                "plan",
                "design",
                "architecture",
                "approach",
                "strategy",
                "how to",
            ]
        ):
            return "plan"

        if any(
            kw in task_lower
            for kw in ["implement", "code", "build", "create", "develop", "write code"]
        ):
            return "code"

        if any(
            kw in task_lower
            for kw in ["test", "verify", "validate", "check", "pytest", "unittest"]
        ):
            return "test"

        if any(
            kw in task_lower
            for kw in ["build", "compile", "install", "setup", "dependencies"]
        ):
            return "build"

        if any(
            kw in task_lower
            for kw in ["review", "audit", "analyze", "assess", "evaluate", "quality"]
        ):
            return "review"

        # Default to explore for general queries
        logger.info(f"No specific routing match, defaulting to 'explore' agent")
        return "explore"

    def list_agents(self) -> Dict[str, str]:
        """
        List all available agents with their descriptions.

        Returns:
            Dict mapping agent type to description
        """
        return {
            agent_type: agent_class.description
            for agent_type, agent_class in self.agents.items()
        }

    def register_agent(self, agent_type: str, agent_class: Type[BaseSubAgent]):
        """
        Register a new agent type.

        Args:
            agent_type: Identifier for the agent
            agent_class: Agent class to register
        """
        if agent_type in self.agents:
            logger.warning(f"Overwriting existing agent type: {agent_type}")

        self.agents[agent_type] = agent_class
        logger.info(f"✅ Registered {agent_type} agent: {agent_class.__name__}")
