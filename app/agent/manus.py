from typing import Dict, List, Optional

from pydantic import Field, model_validator

from app.agent.browser import BrowserContextHelper
from app.agent.toolcall import ToolCallAgent
from app.config import config
from app.logger import logger
from app.prompt.manus import NEXT_STEP_PROMPT, SYSTEM_PROMPT
from app.schema import Message
from app.tool import Terminate, ToolCollection
from app.tool.ask_human import AskHuman
from app.tool.browser_use_tool import BrowserUseTool
from app.tool.mcp import MCPClients, MCPClientTool
from app.tool.python_execute import PythonExecute
from app.tool.str_replace_editor import StrReplaceEditor


class Manus(ToolCallAgent):
    """A versatile general-purpose agent with support for both local and MCP tools."""

    name: str = "Manus"
    description: str = "A versatile agent that can solve various tasks using multiple tools including MCP-based tools"

    system_prompt: str = SYSTEM_PROMPT.format(directory=config.workspace_root)
    next_step_prompt: str = NEXT_STEP_PROMPT

    max_observe: int = 10000

    # Phase 2/3: Configurable max_steps based on effort level
    # Will be set in __init__ based on config.agent settings
    max_steps: int = 20  # Default, overridden by config

    # MCP clients for remote tool access
    mcp_clients: MCPClients = Field(default_factory=MCPClients)

    # Add general-purpose tools to the tool collection
    available_tools: ToolCollection = Field(
        default_factory=lambda: ToolCollection(
            PythonExecute(),
            BrowserUseTool(),
            StrReplaceEditor(),
            AskHuman(),
            Terminate(),
        )
    )

    special_tool_names: list[str] = Field(default_factory=lambda: [Terminate().name])
    browser_context_helper: Optional[BrowserContextHelper] = None

    # Track connected MCP servers
    connected_servers: Dict[str, str] = Field(
        default_factory=dict
    )  # server_id -> url/command
    _initialized: bool = False

    @model_validator(mode="after")
    def initialize_helper(self) -> "Manus":
        """
        Initialize basic components synchronously.

        Phase 2/3: Apply high-effort mode settings from config.
        """
        self.browser_context_helper = BrowserContextHelper(self)

        # Apply high-effort mode from config if enabled
        if hasattr(config, "agent") and config.agent:
            high_effort = getattr(config.agent, "high_effort_mode", False)
            if high_effort:
                # Use high-effort max_steps
                self.max_steps = getattr(config.agent, "max_steps_high_effort", 50)
                self.effort_level = "high"
                logger.info(f"High-effort mode enabled: max_steps={self.max_steps}")
            else:
                # Use normal max_steps
                self.max_steps = getattr(config.agent, "max_steps_normal", 20)
                self.effort_level = "normal"

        return self

    @classmethod
    async def create(cls, **kwargs) -> "Manus":
        """Factory method to create and properly initialize a Manus instance."""
        instance = cls(**kwargs)
        await instance.initialize_mcp_servers()
        instance._initialized = True
        return instance

    async def initialize_mcp_servers(self) -> None:
        """Initialize connections to configured MCP servers."""
        for server_id, server_config in config.mcp_config.servers.items():
            try:
                if server_config.type == "sse":
                    if server_config.url:
                        await self.connect_mcp_server(server_config.url, server_id)
                        logger.info(
                            f"Connected to MCP server {server_id} at {server_config.url}"
                        )
                elif server_config.type == "stdio":
                    if server_config.command:
                        await self.connect_mcp_server(
                            server_config.command,
                            server_id,
                            use_stdio=True,
                            stdio_args=server_config.args,
                        )
                        logger.info(
                            f"Connected to MCP server {server_id} using command {server_config.command}"
                        )

                        # Phase 3: Enhanced tool discovery logging
                        server_tools = [
                            t
                            for t in self.mcp_clients.tools
                            if hasattr(t, "server_id") and t.server_id == server_id
                        ]
                        if server_tools:
                            logger.info(
                                f"📦 Discovered {len(server_tools)} tools from {server_id}:"
                            )
                            for tool in server_tools:
                                # Truncate description for cleaner logs
                                desc = (
                                    tool.description[:80] + "..."
                                    if len(tool.description) > 80
                                    else tool.description
                                )
                                logger.info(f"  - {tool.name}: {desc}")
                        else:
                            logger.warning(f"No tools discovered from {server_id}")
            except Exception as e:
                logger.error(f"Failed to connect to MCP server {server_id}: {e}")

    async def connect_mcp_server(
        self,
        server_url: str,
        server_id: str = "",
        use_stdio: bool = False,
        stdio_args: List[str] = None,
    ) -> None:
        """Connect to an MCP server and add its tools."""
        if use_stdio:
            await self.mcp_clients.connect_stdio(
                server_url, stdio_args or [], server_id
            )
            self.connected_servers[server_id or server_url] = server_url
        else:
            await self.mcp_clients.connect_sse(server_url, server_id)
            self.connected_servers[server_id or server_url] = server_url

        # Update available tools with only the new tools from this server
        new_tools = [
            tool for tool in self.mcp_clients.tools if tool.server_id == server_id
        ]
        self.available_tools.add_tools(*new_tools)

    async def disconnect_mcp_server(self, server_id: str = "") -> None:
        """Disconnect from an MCP server and remove its tools."""
        await self.mcp_clients.disconnect(server_id)
        if server_id:
            self.connected_servers.pop(server_id, None)
        else:
            self.connected_servers.clear()

        # Rebuild available tools without the disconnected server's tools
        base_tools = [
            tool
            for tool in self.available_tools.tools
            if not isinstance(tool, MCPClientTool)
        ]
        self.available_tools = ToolCollection(*base_tools)
        self.available_tools.add_tools(*self.mcp_clients.tools)

    async def cleanup(self):
        """Clean up Manus agent resources."""
        if self.browser_context_helper:
            await self.browser_context_helper.cleanup_browser()
        # Disconnect from all MCP servers only if we were initialized
        if self._initialized:
            await self.disconnect_mcp_server()
            self._initialized = False

    async def think(self) -> bool:
        """Process current state and decide next actions with appropriate context."""
        if not self._initialized:
            await self.initialize_mcp_servers()
            self._initialized = True

        # Phase 3: Self-Reflection Loop for High-Effort Mode
        # Inject reflection prompt every 5 steps to encourage course correction
        if hasattr(config, "agent") and config.agent:
            enable_reflection = getattr(config.agent, "enable_reflection", False)
            high_effort = getattr(config.agent, "high_effort_mode", False)

            if enable_reflection and high_effort:
                current_step = self.current_step
                # Inject reflection every 5 steps (at steps 5, 10, 15, ...)
                if current_step > 0 and current_step % 5 == 0:
                    reflection_prompt = f"""
## 🔄 Reflection Checkpoint (Step {current_step}/{self.max_steps})

Before proceeding, take a moment to reflect:

1. **Progress Review**: What have you accomplished in the last 5 steps?
2. **Approach Validation**: Is your current approach working well, or should you adjust?
3. **Quality Check**: Are you maintaining high quality standards (error handling, edge cases, testing)?
4. **Remaining Work**: What remains to be done? Are you on track?
5. **Improvements**: Are there better tools or methods you should use going forward?

Briefly summarize your reflection, then continue with the next step.
"""
                    # Inject reflection as a system-level message
                    reflection_msg = Message.system_message(reflection_prompt)
                    self.memory.messages.append(reflection_msg)
                    logger.info(f"💭 Injected reflection prompt at step {current_step}")

        original_prompt = self.next_step_prompt
        recent_messages = self.memory.messages[-3:] if self.memory.messages else []
        browser_in_use = any(
            tc.function.name == BrowserUseTool().name
            for msg in recent_messages
            if msg.tool_calls
            for tc in msg.tool_calls
        )

        if browser_in_use:
            self.next_step_prompt = (
                await self.browser_context_helper.format_next_step_prompt()
            )

        result = await super().think()

        # Restore original prompt
        self.next_step_prompt = original_prompt

        return result
