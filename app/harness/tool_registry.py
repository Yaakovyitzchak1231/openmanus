from typing import Dict, List

from app.tool.base import BaseTool
from app.tool.tool_collection import ToolCollection


class ToolRegistry:
    def __init__(self, *tools: BaseTool) -> None:
        self._sources: Dict[str, str] = {}
        self._collection = ToolCollection(*tools)
        for tool in tools:
            self._sources[tool.name] = "local"

    @property
    def collection(self) -> ToolCollection:
        return self._collection

    def add_tools(self, *tools: BaseTool, source: str = "local") -> None:
        for tool in tools:
            if tool.name in self._sources:
                continue
            self._collection.add_tool(tool)
            self._sources[tool.name] = source

    def remove_by_source(self, source: str) -> None:
        keep_tools = [
            tool
            for tool in self._collection.tools
            if self._sources.get(tool.name) != source
        ]
        self._collection = ToolCollection(*keep_tools)
        self._sources = {
            tool.name: self._sources.get(tool.name, "local") for tool in keep_tools
        }

    def remove_by_source_prefix(self, prefix: str) -> None:
        keep_tools = [
            tool
            for tool in self._collection.tools
            if not self._sources.get(tool.name, "").startswith(prefix)
        ]
        self._collection = ToolCollection(*keep_tools)
        self._sources = {
            tool.name: self._sources.get(tool.name, "local") for tool in keep_tools
        }

    def list_tools(self) -> List[Dict[str, str]]:
        return [
            {
                "name": tool.name,
                "description": tool.description or "",
                "source": self._sources.get(tool.name, "local"),
            }
            for tool in self._collection.tools
        ]
