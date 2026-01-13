from typing import Dict, List, Optional

from pydantic import Field, model_validator

from app.agent.browser import BrowserContextHelper
from app.agent.toolcall import ToolCallAgent
from app.config import config
from app.harness.tool_registry import ToolRegistry
from app.logger import logger
from app.memory import ContextManager, MemoryTool
from app.prompt.manus import NEXT_STEP_PROMPT, SYSTEM_PROMPT
from app.schema import Message
from app.tool import Bash, Terminate, ToolCollection
from app.tool.ask_human import AskHuman
from app.tool.browser_use_tool import BrowserUseTool
from app.tool.mcp_code_execution import MCPCodeExecution
from app.tool.mcp import MCPClients
from app.tool.python_execute import PythonExecute
from app.tool.str_replace_editor import StrReplaceEditor
from app.tool.task import TaskTool
from app.tool.tool_search import ToolSearchTool
from app.harness.subagent_registry import SubAgentRegistry


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

    tool_registry: ToolRegistry = Field(
        default_factory=lambda: ToolRegistry(
            PythonExecute(),
            Bash(),
            BrowserUseTool(),
            StrReplaceEditor(),
            AskHuman(),
            Terminate(),
        )
    )
    available_tools: ToolCollection = Field(default_factory=ToolCollection)

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
        self.available_tools = self.tool_registry.collection

        self.tool_registry.add_tools(
            ToolSearchTool(
                tools_provider=lambda: list(self.tool_registry.collection.tools)
            ),
            source="local",
        )
        self.tool_registry.add_tools(
            MCPCodeExecution(mcp_clients=self.mcp_clients, settings=config.mcp_config.code_execution),
            source="local",
        )

        # Phase 0: Add Task tool for spawning specialized sub-agents
        self.tool_registry.add_tools(
            TaskTool(subagent_registry=SubAgentRegistry()),
            source="local",
        )

        # Phase 1: Add Memory tool for persistent storage
        memory_db_path = "workspace/memory.db"
        if hasattr(config, "memory") and config.memory:
            memory_db_path = getattr(config.memory, "db_path", memory_db_path)
        self.tool_registry.add_tools(
            MemoryTool(db_path=memory_db_path),
            source="local",
        )

        self.available_tools = self.tool_registry.collection
        self.use_tool_search = True
        self.core_tool_names = [
            "tool_search",
            "task",  # Add task tool to core tools
            "memory",  # Add memory tool to core tools
            StrReplaceEditor().name,
            Bash().name,
            PythonExecute().name,
            AskHuman().name,
            Terminate().name,
        ]

        # Phase 1: Initialize context manager for long-running agents
        memory_enabled = True
        compaction_threshold = 100000
        compaction_strategy = "simple"
        if hasattr(config, "memory") and config.memory:
            memory_enabled = getattr(config.memory, "enabled", True)
            compaction_threshold = getattr(config.memory, "compaction_threshold_tokens", 100000)
            compaction_strategy = getattr(config.memory, "strategy", "simple")

        if memory_enabled:
            self.context_manager = ContextManager(
                compaction_threshold_tokens=compaction_threshold,
                strategy=compaction_strategy,
            )
            logger.info(f"Context manager enabled: threshold={compaction_threshold}, strategy={compaction_strategy}")

        # Apply effort level from config
        if hasattr(config, "agent") and config.agent:
            effort = getattr(config.agent, "effort_level", "medium")
            if effort in ["low", "medium", "high"]:
                self.effort_level = effort
                logger.info(f"Effort level set to: {self.effort_level} (effective max_steps={self.effective_max_steps})")

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
        server_key = server_id or server_url
        new_tools = [
            tool for tool in self.mcp_clients.tools if tool.server_id == server_id
        ]
        self.tool_registry.add_tools(*new_tools, source=f"mcp:{server_key}")
        self.available_tools = self.tool_registry.collection

    async def disconnect_mcp_server(self, server_id: str = "") -> None:
        """Disconnect from an MCP server and remove its tools."""
        await self.mcp_clients.disconnect(server_id)
        if server_id:
            self.connected_servers.pop(server_id, None)
        else:
            self.connected_servers.clear()

        if server_id:
            self.tool_registry.remove_by_source(f"mcp:{server_id}")
        else:
            self.tool_registry.remove_by_source_prefix("mcp:")
        self.available_tools = self.tool_registry.collection

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

        # Phase 2 FIX: Self-Reflection with single updatable marker (prevents accumulation)
        # Instead of appending new reflection prompts that pile up, we update a single marker
        if hasattr(config, "agent") and config.agent:
            enable_reflection = getattr(config.agent, "enable_reflection", False)
            high_effort = getattr(config.agent, "high_effort_mode", False)

            if enable_reflection and high_effort:
                current_step = self.current_step
                # Update reflection marker every 5 steps (at steps 5, 10, 15, ...)
                if current_step > 0 and current_step % 5 == 0:
                    # Single lightweight reflection marker
                    reflection_content = (
                        f"[Reflection checkpoint: step {current_step}/{self.max_steps}] "
                        f"Review progress, validate approach, check quality, plan next steps."
                    )

                    # Remove any previous reflection markers to prevent accumulation
                    self.memory.messages = [
                        msg for msg in self.memory.messages
                        if not (msg.role == "system" and "[Reflection checkpoint:" in (msg.content or ""))
                    ]

                    # Add single updated reflection marker
                    self.memory.messages.append(Message.system_message(reflection_content))
                    logger.debug(f"Reflection checkpoint at step {current_step}")

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
