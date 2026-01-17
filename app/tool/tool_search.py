from __future__ import annotations

import json
import re
from typing import Callable, Iterable, List, Literal

from pydantic import Field

from app.tool.base import BaseTool, ToolResult


ToolSearchDetail = Literal["names", "schemas"]


def _tokenize_query(query: str) -> List[str]:
    cleaned = re.sub(r"[^a-zA-Z0-9_\\-\\s]", " ", query.lower())
    return [token for token in cleaned.split() if token]


class ToolSearchTool(BaseTool):
    """
    A lightweight tool index searcher.

    This mirrors the "Tool Search Tool" concept from Anthropic's advanced tool
    use guidance: keep a small, stable core toolset in the model context, then
    discover additional tools on-demand.
    """

    name: str = "tool_search"
    description: str = (
        "Search available tools by name/description to load only the tools "
        "needed for the current task. Returns matching tool names and short "
        "descriptions; can optionally return schemas."
    )
    parameters: dict = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Search query describing the capability needed.",
            },
            "max_results": {
                "type": "integer",
                "description": "Maximum number of tools to return.",
                "default": 8,
            },
            "detail": {
                "type": "string",
                "enum": ["names", "schemas"],
                "description": "Return tool names/descriptions or include schemas.",
                "default": "names",
            },
        },
        "required": ["query"],
    }

    tools_provider: Callable[[], Iterable[BaseTool]] = Field(exclude=True)

    def _score(self, query_tokens: List[str], tool: BaseTool) -> int:
        haystack = f"{tool.name} {tool.description or ''}".lower()
        score = 0
        for token in query_tokens:
            if token in haystack:
                score += 3
        return score

    async def execute(
        self,
        query: str,
        max_results: int = 8,
        detail: ToolSearchDetail = "names",
        **kwargs,
    ) -> ToolResult:
        q = (query or "").strip()
        if not q:
            return self.fail_response("query is required")

        tokens = _tokenize_query(q)
        tools = list(self.tools_provider())
        scored = []
        for tool in tools:
            if not getattr(tool, "name", None):
                continue
            if tool.name == self.name:
                continue
            score = self._score(tokens, tool)
            if score > 0:
                scored.append((score, tool))

        scored.sort(key=lambda item: item[0], reverse=True)
        best = [tool for _, tool in scored[: max(1, int(max_results or 8))]]

        matches = []
        for tool in best:
            entry = {
                "name": tool.name,
                "description": tool.description or "",
            }
            if detail == "schemas":
                entry["schema"] = tool.to_param()
            matches.append(entry)

        payload = {
            "query": q,
            "count": len(matches),
            "matches": matches,
            "note": (
                "Call tool_search whenever you need a capability that isn't in your "
                "currently loaded tool list. The harness will make the returned tools "
                "available in the next step."
            ),
        }
        return ToolResult(output=json.dumps(payload, ensure_ascii=False, indent=2))
