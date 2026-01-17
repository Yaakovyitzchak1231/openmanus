"""
Build Agent

Build verification and dependency checking. Specialized in verifying build processes,
checking dependencies, and validating setup.
"""

from pydantic import Field

from app.agent.subagents.base_subagent import BaseSubAgent
from app.tool import Terminate
from app.tool.bash import Bash
from app.tool.python_execute import PythonExecute
from app.tool.tool_collection import ToolCollection


BUILD_SYSTEM_PROMPT = """You are a Build Agent specialized in build verification and dependency management.

Your capabilities:
- Verify build processes and compilation
- Check and install dependencies
- Validate project setup (requirements.txt, package.json, etc.)
- Run build commands (npm build, python setup.py, etc.)
- Identify missing dependencies or build errors
- Verify environment configuration

Your approach:
1. **Detect**: Identify project type (Python, Node.js, etc.)
2. **Check**: Verify dependencies are installed
3. **Install**: Install missing dependencies if needed
4. **Build**: Run build commands
5. **Validate**: Ensure build completes successfully
6. **Report**: Provide build status and any issues

Common Tasks:
- Python: pip install -r requirements.txt, python setup.py build
- Node.js: npm install, npm build, npm run build
- Verify imports: python -c "import package_name"
- Check versions: python --version, node --version, npm --version

Build Status Checks:
- Dependencies installed correctly
- Build completes without errors
- All required packages available
- Environment variables set
- Configuration files valid

When complete, use the Terminate tool with a summary of:
- Build status (SUCCESS/FAILED)
- Dependencies verified
- Any installation or build errors
- Recommendations for fixes"""

BUILD_NEXT_STEP_PROMPT = """Continue build verification.

Remember to:
- Check all dependencies
- Run build commands
- Verify environment
- Report build status
- Use Terminate when verification is complete"""


class BuildAgent(BaseSubAgent):
    """
    Build Agent for build verification and dependency management.

    Optimized for:
    - Dependency checking and installation
    - Build process execution
    - Environment validation
    - Setup verification

    Configured for quick build checks.
    """

    name: str = "build_agent"
    description: str = "Build verification and dependency management specialist"
    agent_type: str = "build"

    # Configuration for build verification
    max_steps: int = Field(default=10, description="Quick build verification")
    effort_level: str = Field(default="normal", description="Normal effort for builds")

    # Specialized prompts
    system_prompt: str = BUILD_SYSTEM_PROMPT
    next_step_prompt: str = BUILD_NEXT_STEP_PROMPT

    # Tool set for build verification
    available_tools: ToolCollection = Field(
        default_factory=lambda: ToolCollection(
            Bash(),  # For pip, npm, build commands
            PythonExecute(),  # For checking imports, running scripts
            Terminate(),  # To signal completion
        )
    )

    def __init__(self, **data):
        """Initialize Build Agent with build configuration"""
        data.setdefault("name", "build_agent")
        data.setdefault("agent_type", "build")
        super().__init__(**data)
