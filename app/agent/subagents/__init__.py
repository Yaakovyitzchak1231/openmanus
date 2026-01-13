"""
Sub-Agents Module

Specialized agents that can be spawned by the main orchestrator via the Task tool.
Each sub-agent has specific capabilities and prompts optimized for its purpose.

Available Sub-Agents:
- ExploreAgent: Fast codebase exploration (10 steps)
- PlanAgent: Implementation planning (20 steps)
- CodingAgent: Long-running coding with Initializer/Coding modes (50 steps)
- TestAgent: Automated testing and validation (15 steps)
- BuildAgent: Build verification and dependencies (10 steps)
"""

from app.agent.subagents.base_subagent import BaseSubAgent
from app.agent.subagents.build_agent import BuildAgent
from app.agent.subagents.coding_agent import CodingAgent
from app.agent.subagents.explore_agent import ExploreAgent
from app.agent.subagents.plan_agent import PlanAgent
from app.agent.subagents.test_agent import TestAgent


__all__ = [
    "BaseSubAgent",
    "ExploreAgent",
    "PlanAgent",
    "CodingAgent",
    "TestAgent",
    "BuildAgent",
]
