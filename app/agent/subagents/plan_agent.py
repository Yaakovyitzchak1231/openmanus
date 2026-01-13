"""
Plan Agent

Implementation planning and architecture design. Specialized in analyzing requirements,
designing implementation strategies, and considering trade-offs.
"""

from pydantic import Field

from app.agent.subagents.base_subagent import BaseSubAgent
from app.tool import Terminate
from app.tool.bash import Bash
from app.tool.tool_collection import ToolCollection


PLAN_SYSTEM_PROMPT = """You are a Plan Agent specialized in software architecture and implementation planning.

Your capabilities:
- Analyze requirements and break down into tasks
- Design implementation strategies
- Consider architectural trade-offs
- Identify dependencies and sequencing
- Recommend file structures and patterns
- Assess complexity and risks

Your approach:
1. **Understand**: Thoroughly analyze the requirements and constraints
2. **Explore**: Survey existing code patterns and architecture (if applicable)
3. **Design**: Create a clear, step-by-step implementation plan
4. **Consider**: Think through edge cases, risks, and alternatives
5. **Document**: Present a structured plan with:
   - Overview and goals
   - Step-by-step implementation sequence
   - Critical files to modify/create
   - Dependencies and requirements
   - Testing and verification approach
   - Potential risks and mitigations

Output Format:
Provide your plan in a structured format with clear sections. Be specific about:
- What needs to be built
- Which files to modify/create
- In what order tasks should be done
- How to verify success

When your plan is complete, use the Terminate tool."""

PLAN_NEXT_STEP_PROMPT = """Continue developing the implementation plan.

Consider:
- Have you fully understood the requirements?
- Have you explored the existing codebase?
- Is your plan detailed and actionable?
- Have you identified risks?
- Is the testing approach clear?

Use Terminate when your plan is comprehensive and ready for implementation."""


class PlanAgent(BaseSubAgent):
    """
    Plan Agent for implementation planning and architecture design.

    Optimized for:
    - Requirements analysis
    - Architecture design
    - Implementation strategy
    - Trade-off analysis
    - Risk assessment

    Configured for thorough planning with more steps.
    """

    name: str = "plan_agent"
    description: str = "Architecture and implementation planning specialist"
    agent_type: str = "plan"

    # Configuration for thorough planning
    max_steps: int = Field(default=20, description="More steps for thorough planning")
    effort_level: str = Field(
        default="high", description="High effort for quality planning"
    )

    # Specialized prompts
    system_prompt: str = PLAN_SYSTEM_PROMPT
    next_step_prompt: str = PLAN_NEXT_STEP_PROMPT

    # Tool set for planning
    available_tools: ToolCollection = Field(
        default_factory=lambda: ToolCollection(
            Bash(),  # For exploring codebase structure, reading files with cat
            Terminate(),  # To signal completion
        )
    )

    def __init__(self, **data):
        """Initialize Plan Agent with planning configuration"""
        data.setdefault("name", "plan_agent")
        data.setdefault("agent_type", "plan")
        super().__init__(**data)
