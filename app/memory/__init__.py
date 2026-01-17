"""
Memory module for long-running agents.

Provides context management and persistent storage that works with any LLM provider.

Components:
- ContextManager: Manages context window, triggers compaction when needed
- MemoryTool: Persistent SQLite storage for important information
- Compaction Strategies: Various methods to reduce context size

Usage:
    from app.memory import ContextManager, MemoryTool

    # Create context manager
    cm = ContextManager(compaction_threshold_tokens=100000)

    # In agent run loop:
    messages = await cm.compact_if_needed(messages, llm)

    # For persistent storage:
    memory_tool = MemoryTool()
    await memory_tool.execute("store", key="decision_1", value="Use SQLite", category="decisions")
"""

from .compaction_strategies import (
    CompactionStrategy,
    CompositeStrategy,
    MessageSummarizer,
    SelectiveRetention,
    ThinkingClearer,
    ToolResultClearer,
)
from .context_manager import ContextManager
from .memory_tool import MemoryTool


__all__ = [
    "ContextManager",
    "MemoryTool",
    "CompactionStrategy",
    "ToolResultClearer",
    "ThinkingClearer",
    "MessageSummarizer",
    "SelectiveRetention",
    "CompositeStrategy",
]
