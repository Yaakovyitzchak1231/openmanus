"""
Coding Agent

Long-running coding with Initializer/Coding dual-mode pattern. This implements the
Claude Opus 4.5 long-running agent pattern from the effective-harnesses documentation.

Two modes:
1. Initializer Mode: First session - sets up environment (init.sh, feature_list.json, claude-progress.txt)
2. Coding Mode: Subsequent sessions - incremental feature implementation with testing and commits
"""

from typing import Literal, Optional

from pydantic import Field

from app.agent.subagents.base_subagent import BaseSubAgent
from app.tool import Terminate
from app.tool.bash import Bash
from app.tool.browser_use_tool import BrowserUseTool
from app.tool.python_execute import PythonExecute
from app.tool.str_replace_editor import StrReplaceEditor
from app.tool.test_runner import TestRunner
from app.tool.tool_collection import ToolCollection


INITIALIZER_SYSTEM_PROMPT = """You are a Coding Agent in INITIALIZER MODE - setting up a project for long-running development.

Your mission: Set up the environment for incremental feature development across multiple sessions.

CRITICAL TASKS (you must complete ALL of these):

1. **Create init.sh** - Initialization script that:
   - Starts development server(s)
   - Runs basic validation
   - Sets up environment
   - Can be run at the start of each session

2. **Create feature_list.json** - Comprehensive feature list (100-200+ features):
   - Break down the project spec into specific, testable features
   - Each feature: {{"category": "functional/ui/backend", "description": "...", "steps": ["..."], "passes": false}}
   - Mark ALL as "passes": false initially
   - Be thorough - include every feature needed

3. **Create claude-progress.txt** - Session log:
   - Initialize with timestamp and "Project initialized"
   - This will track progress across sessions

4. **Make initial git commit**:
   - git add .
   - git commit -m "Initial project setup by Coding Agent (Initializer)"

**Format for feature_list.json**:
```json
[
  {{
    "category": "functional",
    "description": "User can create a new chat",
    "steps": [
      "Click 'New Chat' button",
      "Verify new conversation appears",
      "Check chat area shows welcome state"
    ],
    "passes": false
  }}
]
```

After completing ALL 4 tasks, use Terminate with summary of what was created."""

CODING_SYSTEM_PROMPT = """You are a Coding Agent in CODING MODE - making incremental progress on features.

Your approach (FOLLOW THIS EXACTLY EVERY SESSION):

**PHASE 1: Get Your Bearings** (ALWAYS START HERE)
1. Run `pwd` to see current directory
2. Read claude-progress.txt to see recent work
3. Read feature_list.json to see what's done/pending
4. Run `git log --oneline -20` to see recent commits

**PHASE 2: Initialize Environment**
5. Run `bash init.sh` to start servers and validate setup
6. Test basic functionality (use browser automation if web app)

**PHASE 3: Choose ONE Feature**
7. Pick the HIGHEST PRIORITY feature with "passes": false
8. Work on ONLY ONE feature at a time

**PHASE 4: Implement Feature**
9. Implement the feature with clean, working code
10. Test thoroughly - use browser automation for web features
11. Ensure code works end-to-end

**PHASE 5: Update and Commit**
12. Update feature_list.json - change ONLY the completed feature to "passes": true
13. Commit your work: `git add . && git commit -m "Implement [feature description]"`
14. Append to claude-progress.txt with timestamp and what was done

**CRITICAL RULES**:
- Work on ONE feature at a time (not multiple)
- ALWAYS test end-to-end before marking as passing
- NEVER remove or edit features from feature_list.json (only change "passes" field)
- Leave code in clean state (no bugs, well-documented)
- Use browser automation (BrowserUseTool) for web app testing
- If a feature fails, leave as "passes": false and document the issue

When you've completed a feature (implemented + tested + committed), use Terminate."""

CODING_NEXT_STEP_PROMPT = """Continue working on the current feature.

Remember:
- Test thoroughly before marking complete
- Use browser automation for end-to-end validation
- Commit when feature is fully working
- Update progress log"""


class CodingAgent(BaseSubAgent):
    """
    Coding Agent with Initializer/Coding dual-mode pattern.

    This implements the Claude Opus 4.5 long-running agent pattern for
    work across multiple context windows.

    **Initializer Mode** (first session):
    - Creates init.sh, feature_list.json, claude-progress.txt
    - Makes initial git commit
    - Sets up environment for incremental work

    **Coding Mode** (subsequent sessions):
    - Reads git logs, progress, feature list
    - Works on ONE feature at a time
    - Tests end-to-end (browser automation)
    - Commits + logs progress

    This enables agents to work consistently across many context windows
    without losing track of progress.
    """

    name: str = "coding_agent"
    description: str = (
        "Long-running coding with session management (Initializer/Coding modes)"
    )
    agent_type: str = "code"

    # Dual mode configuration
    mode: Literal["initializer", "coding"] = Field(
        default="coding",
        description="Agent mode: 'initializer' for first session, 'coding' for subsequent sessions",
    )

    # Configuration for long-running coding
    max_steps: int = Field(default=50, description="Long-running coding sessions")
    effort_level: str = Field(
        default="high", description="High effort for quality implementation"
    )

    # File paths (configurable)
    init_script_path: str = Field(
        default="init.sh", description="Path to initialization script"
    )
    feature_list_path: str = Field(
        default="feature_list.json", description="Path to feature tracking file"
    )
    progress_log_path: str = Field(
        default="claude-progress.txt", description="Path to progress log"
    )

    # Tool set for coding (comprehensive)
    available_tools: ToolCollection = Field(
        default_factory=lambda: ToolCollection(
            Bash(),  # For git, file operations, running servers
            PythonExecute(),  # For executing Python code
            StrReplaceEditor(),  # For editing files
            BrowserUseTool(),  # For end-to-end testing
            TestRunner(),  # For running tests
            Terminate(),  # To signal completion
        )
    )

    def __init__(self, **data):
        """Initialize Coding Agent with mode-specific configuration"""
        data.setdefault("name", "coding_agent")
        data.setdefault("agent_type", "code")

        # Determine mode from context if provided
        if "task_context" in data and data["task_context"]:
            mode = data["task_context"].get("mode", "coding")
            data.setdefault("mode", mode)

        super().__init__(**data)

        # Set mode-specific system prompt
        if self.mode == "initializer":
            self.system_prompt = INITIALIZER_SYSTEM_PROMPT
        else:
            self.system_prompt = CODING_SYSTEM_PROMPT

        self.next_step_prompt = CODING_NEXT_STEP_PROMPT

    async def run(self, request: Optional[str] = None) -> str:
        """
        Run the Coding Agent in its configured mode.

        Initializer mode: Sets up environment
        Coding mode: Implements features incrementally
        """
        # Add mode context to the task description
        mode_prefix = f"[{self.mode.upper()} MODE] "
        enhanced_request = request or self.task_description

        if not enhanced_request.startswith(mode_prefix):
            enhanced_request = mode_prefix + enhanced_request

        return await super().run(enhanced_request)
