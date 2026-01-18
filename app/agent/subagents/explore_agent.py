"""
Explore Agent

Fast codebase exploration and understanding. Specialized in finding files, searching
for patterns, and quickly understanding code structure without extensive analysis.
"""

from pydantic import Field

from app.agent.subagents.base_subagent import BaseSubAgent
from app.tool import Terminate
from app.tool.bash import Bash
from app.tool.tool_collection import ToolCollection


EXPLORE_SYSTEM_PROMPT = """You are an Explore Agent specialized in fast codebase exploration and search.

Your capabilities:
- Find files matching patterns (use ls, find, grep commands)
- Search code for keywords, classes, functions
- Understand directory structure quickly
- Identify relevant files for a task
- Provide concise summaries of findings

Your approach:
1. Start with broad searches (directory structure, file patterns)
2. Narrow down to specific files or code sections
3. Read only what's necessary - be efficient
4. Summarize findings clearly and concisely

You have a LIMITED number of steps (max 10) so be efficient:
- Use grep/find for pattern matching instead of reading many files
- Focus on answering the specific question asked
- Don't explore beyond what's needed

When complete, use the Terminate tool to finish."""

EXPLORE_NEXT_STEP_PROMPT = """Continue exploring the codebase to answer the task.

Remember to:
- Be targeted in your searches
- Don't read unnecessary files
- Summarize what you've found
- Use Terminate when you have enough information"""


class ExploreAgent(BaseSubAgent):
    """
    Explore Agent for fast codebase search and understanding.

    Optimized for:
    - Quick file discovery
    - Pattern searching
    - Code structure understanding
    - Targeted information gathering

    Limited to 10 steps for efficiency.
    """

    name: str = "explore_agent"
    description: str = "Fast codebase exploration and search specialist"
    agent_type: str = "explore"

    # Optimized configuration for fast exploration
    max_steps: int = Field(default=10, description="Fast exploration - limited steps")
    effort_level: str = Field(default="normal", description="Normal effort for speed")

    # Specialized prompts
    system_prompt: str = EXPLORE_SYSTEM_PROMPT
    next_step_prompt: str = EXPLORE_NEXT_STEP_PROMPT

    # Minimal tool set for exploration
    available_tools: ToolCollection = Field(
        default_factory=lambda: ToolCollection(
            Bash(),  # For find, grep, ls, cat commands
            Terminate(),  # To signal completion
        )
    )

    def __init__(self, **data):
        """Initialize Explore Agent with exploration configuration"""
        # Set defaults before calling super().__init__
        data.setdefault("name", "explore_agent")
        data.setdefault("agent_type", "explore")
        super().__init__(**data)
