"""
Context compaction strategies - LLM-agnostic implementation.

All strategies work client-side and are compatible with any LLM provider.

Strategies:
- ToolResultClearer: Remove old tool results, keep recent N
- ThinkingClearer: Remove intermediate reasoning blocks
- MessageSummarizer: LLM-based summarization (works with any model)
- SelectiveRetention: Keep system prompts + recent turns + user queries
"""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from pydantic import BaseModel, Field


if TYPE_CHECKING:
    from app.schema import Message


class CompactionStrategy(ABC, BaseModel):
    """Base class for context compaction strategies"""

    name: str = Field(default="base", description="Strategy name")

    class Config:
        arbitrary_types_allowed = True

    @abstractmethod
    async def apply(self, messages: List["Message"]) -> List["Message"]:
        """
        Apply compaction strategy to messages.

        Args:
            messages: Current message list

        Returns:
            Compacted message list
        """

    def get_config(self) -> Dict[str, Any]:
        """Get strategy configuration as dict"""
        return self.model_dump(exclude={"name"})


class ToolResultClearer(CompactionStrategy):
    """
    Clears old tool results, keeps only recent N tool use/result pairs.

    Useful for long agent runs with many tool calls where old results
    are no longer relevant.
    """

    name: str = "tool_result_clearer"
    keep_recent: int = Field(
        default=5, description="Number of recent tool results to keep"
    )
    exclude_tools: List[str] = Field(
        default_factory=list, description="Tool names to never clear"
    )
    clear_inputs: bool = Field(
        default=False, description="Also clear tool call inputs (more aggressive)"
    )

    async def apply(self, messages: List["Message"]) -> List["Message"]:
        """Remove old tool results, keeping recent N"""
        # Identify tool messages
        tool_indices = [i for i, m in enumerate(messages) if m.role == "tool"]

        # If we have more tool messages than we want to keep
        if len(tool_indices) > self.keep_recent:
            # Indices of tool messages to remove
            to_remove = set(tool_indices[: -self.keep_recent])

            # Check for excluded tools
            final_remove = set()
            for idx in to_remove:
                msg = messages[idx]
                tool_name = getattr(msg, "name", None)
                if tool_name not in self.exclude_tools:
                    final_remove.add(idx)

            # Build new message list
            return [m for i, m in enumerate(messages) if i not in final_remove]

        return messages


class ThinkingClearer(CompactionStrategy):
    """
    Clears thinking/reasoning content from assistant messages.

    Some LLMs include <thinking> blocks or chain-of-thought reasoning
    that can be removed after processing to save context space.
    """

    name: str = "thinking_clearer"
    keep_recent_turns: int = Field(
        default=2, description="Keep thinking in recent N assistant turns"
    )
    thinking_markers: List[str] = Field(
        default_factory=lambda: [
            "<thinking>",
            "</thinking>",
            "<reasoning>",
            "</reasoning>",
        ],
        description="Markers that indicate thinking content",
    )

    async def apply(self, messages: List["Message"]) -> List["Message"]:
        """Remove thinking blocks from older assistant messages"""
        import re

        # Find assistant message indices
        assistant_indices = [i for i, m in enumerate(messages) if m.role == "assistant"]

        # Keep thinking in recent N turns
        indices_to_clear = (
            assistant_indices[: -self.keep_recent_turns]
            if len(assistant_indices) > self.keep_recent_turns
            else []
        )

        result = []
        for i, msg in enumerate(messages):
            if i in indices_to_clear and msg.content:
                # Remove thinking blocks
                cleaned_content = msg.content
                for start, end in zip(
                    self.thinking_markers[::2], self.thinking_markers[1::2]
                ):
                    pattern = f"{re.escape(start)}.*?{re.escape(end)}"
                    cleaned_content = re.sub(
                        pattern, "", cleaned_content, flags=re.DOTALL
                    )
                # Create new message with cleaned content
                new_msg = msg.model_copy(update={"content": cleaned_content.strip()})
                result.append(new_msg)
            else:
                result.append(msg)

        return result


class MessageSummarizer(CompactionStrategy):
    """
    Client-side compaction with LLM-generated summaries.
    Works with any LLM provider.

    Uses a 5-section summary format to preserve critical context
    while dramatically reducing token count.
    """

    name: str = "message_summarizer"
    summary_model: Optional[str] = Field(
        default=None, description="Model for summaries (None = use main model)"
    )

    # 5-section summary structure
    SUMMARY_SECTIONS: List[str] = [
        "Task Overview: User's core request, success criteria, constraints",
        "Current State: Completed work, files modified, artifacts produced",
        "Important Discoveries: Technical constraints, decisions, errors resolved, failed approaches",
        "Next Steps: Specific actions needed, blockers, priority order",
        "Context to Preserve: User preferences, domain-specific details, commitments",
    ]

    def get_summary_prompt(self) -> str:
        """Generate the summary prompt with 5-section structure"""
        sections = "\n".join(
            f"{i+1}. **{s}**" for i, s in enumerate(self.SUMMARY_SECTIONS)
        )
        return f"""Generate a structured summary of the conversation with these sections:

{sections}

Be concise but thorough. Capture critical technical details and decisions.
Wrap the entire summary in <summary></summary> tags."""

    async def apply(self, messages: List["Message"]) -> List["Message"]:
        """
        This requires LLM call - use ContextManager.summarize_messages() instead.
        Returns messages unchanged when called directly.
        """
        return messages


class SelectiveRetention(CompactionStrategy):
    """
    Keeps system prompts + recent N turns + all user queries.

    A simple but effective strategy that maintains conversation coherence
    while reducing context size. Works without any LLM calls.
    """

    name: str = "selective_retention"
    keep_recent_turns: int = Field(
        default=5, description="Number of recent conversation turns to keep"
    )
    always_keep_system: bool = Field(
        default=True, description="Always keep system messages"
    )
    always_keep_user: bool = Field(
        default=True, description="Always keep user messages"
    )

    async def apply(self, messages: List["Message"]) -> List["Message"]:
        """Apply selective retention"""
        if not messages:
            return messages

        retained = []
        seen_indices = set()

        # First pass: keep system messages and user messages
        for i, msg in enumerate(messages):
            if self.always_keep_system and msg.role == "system":
                retained.append((i, msg))
                seen_indices.add(i)
            elif self.always_keep_user and msg.role == "user":
                retained.append((i, msg))
                seen_indices.add(i)

        # Second pass: add recent turns (approximately 2 messages per turn)
        recent_count = self.keep_recent_turns * 2
        recent_start = max(0, len(messages) - recent_count)

        for i in range(recent_start, len(messages)):
            if i not in seen_indices:
                retained.append((i, messages[i]))
                seen_indices.add(i)

        # Sort by original index to maintain order
        retained.sort(key=lambda x: x[0])

        return [msg for _, msg in retained]


class CompositeStrategy(CompactionStrategy):
    """
    Combines multiple strategies in sequence.

    Strategies are applied in order, allowing for layered compaction.
    """

    name: str = "composite"
    strategies: List[CompactionStrategy] = Field(default_factory=list)

    async def apply(self, messages: List["Message"]) -> List["Message"]:
        """Apply all strategies in sequence"""
        result = messages
        for strategy in self.strategies:
            result = await strategy.apply(result)
        return result
