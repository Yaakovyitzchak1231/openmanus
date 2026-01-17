from __future__ import annotations

from typing import Optional

from pydantic import Field

from app.config import MCPCodeExecutionSettings
from app.logger import logger
from app.tool.base import BaseTool, ToolResult
from app.tool.mcp import MCPClients, MCPClientTool


_CODE_EXEC_DESCRIPTION = """\
Execute code via an MCP server to reduce tool token overhead.

Use this for batch scripts or multi-step command sequences that would otherwise
require many tool calls. This tool routes code to an MCP-exposed execution tool
such as a shell or Python runner.
"""


class MCPCodeExecution(BaseTool):
    name: str = "mcp_code_execution"
    description: str = _CODE_EXEC_DESCRIPTION
    parameters: dict = {
        "type": "object",
        "properties": {
            "code": {
                "type": "string",
                "description": "Code or command script to execute.",
            },
            "language": {
                "type": "string",
                "description": "Language hint (e.g., bash, python).",
            },
            "server_id": {
                "type": "string",
                "description": "Optional MCP server id to target.",
            },
            "tool_name": {
                "type": "string",
                "description": "Optional MCP tool name to target.",
            },
        },
        "required": ["code"],
    }

    mcp_clients: MCPClients = Field(exclude=True)
    settings: MCPCodeExecutionSettings = Field(exclude=True)

    def _normalize_language(self, language: Optional[str]) -> str:
        lang = (language or self.settings.default_language or "").strip().lower()
        return lang or "bash"

    def _language_allowed(self, language: str) -> bool:
        allowed = self.settings.allowed_languages or []
        if not allowed:
            return True
        return language in [lang.lower() for lang in allowed]

    def _enforce_limits(self, code: str) -> Optional[ToolResult]:
        limit = self.settings.max_code_chars
        if limit is None or limit <= 0:
            return None
        if len(code) > limit:
            return self.fail_response(
                f"Code length {len(code)} exceeds max_code_chars limit {limit}."
            )
        return None

    def _matches_tool_name(self, tool: MCPClientTool, target: str) -> bool:
        target_lower = target.lower()
        return target_lower in {
            tool.name.lower(),
            tool.original_name.lower(),
        }

    def _candidate_tools(self, server_id: Optional[str]) -> list[MCPClientTool]:
        tools = [
            tool for tool in self.mcp_clients.tools if isinstance(tool, MCPClientTool)
        ]
        if server_id:
            return [tool for tool in tools if tool.server_id == server_id]
        return tools

    def _select_tool(
        self,
        language: str,
        server_id: Optional[str],
        tool_name: Optional[str],
    ) -> Optional[MCPClientTool]:
        candidates = self._candidate_tools(server_id or self.settings.preferred_server)

        preferred_tool = tool_name or self.settings.preferred_tool
        if preferred_tool:
            for tool in candidates:
                if self._matches_tool_name(tool, preferred_tool):
                    return tool

        keywords = []
        if language in {"python", "py"}:
            keywords = ["python", "py"]
        elif language in {"bash", "shell", "sh", "cmd"}:
            keywords = ["bash", "shell", "sh", "cmd"]
        else:
            keywords = [language]

        def has_code_param(tool: MCPClientTool) -> bool:
            props = (tool.parameters or {}).get("properties", {})
            return any(name in props for name in ("code", "command", "script", "input"))

        scored = []
        for tool in candidates:
            if not has_code_param(tool):
                continue
            name = f"{tool.name} {tool.original_name}".lower()
            score = sum(1 for kw in keywords if kw in name)
            scored.append((score, tool))

        scored.sort(key=lambda item: item[0], reverse=True)
        if scored and scored[0][0] > 0:
            return scored[0][1]

        return scored[0][1] if scored else None

    def _build_payload(self, tool: MCPClientTool, language: str, code: str) -> dict:
        props = (tool.parameters or {}).get("properties", {})
        payload: dict = {}

        if "language" in props:
            payload["language"] = language
        elif "lang" in props:
            payload["lang"] = language

        for candidate in ("code", "command", "script", "input"):
            if candidate in props:
                payload[candidate] = code
                break

        if "timeout" in props:
            payload["timeout"] = self.settings.timeout_seconds

        return payload

    def _truncate_output(self, result: ToolResult) -> ToolResult:
        limit = self.settings.max_output_chars
        if limit is None or limit <= 0:
            return result
        if result.output is None:
            return result
        output_text = str(result.output)
        if len(output_text) <= limit:
            return result
        truncated = output_text[:limit] + "...[truncated]"
        return result.replace(output=truncated)

    async def execute(
        self,
        code: str,
        language: Optional[str] = None,
        server_id: Optional[str] = None,
        tool_name: Optional[str] = None,
    ) -> ToolResult:
        if not self.settings.enabled:
            return self.fail_response(
                "MCP code execution is disabled. Enable it in config.toml under [mcp.code_execution]."
            )

        if not code or not code.strip():
            return self.fail_response("Code is required for MCP execution.")

        lang = self._normalize_language(language)
        if not self._language_allowed(lang):
            return self.fail_response(
                f"Language '{lang}' is not allowed. Allowed: {self.settings.allowed_languages}."
            )

        limit_error = self._enforce_limits(code)
        if limit_error:
            return limit_error

        if not self.mcp_clients.sessions:
            return self.fail_response("No MCP sessions connected.")

        tool = self._select_tool(lang, server_id, tool_name)
        if not tool:
            return self.fail_response(
                "No suitable MCP execution tool found. Configure preferred_server/preferred_tool."
            )

        payload = self._build_payload(tool, lang, code)
        if not payload:
            return self.fail_response(
                f"Tool '{tool.name}' does not accept code or command parameters."
            )

        logger.info(
            "MCP code execution using tool=%s server_id=%s language=%s",
            tool.name,
            tool.server_id,
            lang,
        )
        result = await tool.execute(**payload)
        if isinstance(result, ToolResult):
            return self._truncate_output(result)
        return ToolResult(output=str(result))
