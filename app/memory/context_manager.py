"""
Context Manager for long-running agents - LLM-agnostic implementation.

Works with any LLM provider (OpenAI, Anthropic, OpenRouter, local models, etc.)
Enables 50+ step agent runs without context overflow.
"""

import logging
import re
from typing import TYPE_CHECKING, Any, Dict, List, Literal

from pydantic import BaseModel, Field

from .compaction_strategies import (
    CompactionStrategy,
    MessageSummarizer,
    SelectiveRetention,
    ThinkingClearer,
    ToolResultClearer,
)


if TYPE_CHECKING:
    from app.llm import LLM
    from app.schema import Message

logger = logging.getLogger(__name__)


class ContextManager(BaseModel):
    """
    Manages context window for long-running agents.
    Works with any LLM provider.

    Usage:
        cm = ContextManager(compaction_threshold_tokens=100000)

        # Before each agent step:
        messages = await cm.compact_if_needed(messages, llm)

        # Get stats:
        stats = cm.get_stats()
    """

    # Thresholds
    compaction_threshold_tokens: int = Field(
        default=100000, description="Token threshold to trigger compaction"
    )
    warning_threshold_percent: float = Field(
        default=0.8,
        description="Percentage of threshold to trigger warning (0.8 = 80%)",
    )

    # Strategy configuration
    strategy: Literal["simple", "summarize", "composite"] = Field(
        default="simple",
        description="Compaction strategy: simple (selective retention), summarize (LLM summary), composite (layered)",
    )

    # Strategies
    simple_strategy: SelectiveRetention = Field(
        default_factory=lambda: SelectiveRetention(keep_recent_turns=5)
    )
    summarizer: MessageSummarizer = Field(default_factory=MessageSummarizer)
    composite_strategies: List[CompactionStrategy] = Field(
        default_factory=lambda: [
            ToolResultClearer(keep_recent=5),
            ThinkingClearer(keep_recent_turns=2),
            SelectiveRetention(keep_recent_turns=5),
        ]
    )

    # Tracking metrics
    total_tokens_saved: int = Field(
        default=0, description="Total tokens saved by compaction"
    )
    compaction_count: int = Field(
        default=0, description="Number of compaction operations"
    )
    last_compaction_savings: int = Field(
        default=0, description="Tokens saved in last compaction"
    )

    class Config:
        arbitrary_types_allowed = True

    async def check_context_health(
        self, messages: List["Message"], llm: "LLM"
    ) -> Dict[str, Any]:
        """
        Check current context token usage and health.

        Args:
            messages: Current message list
            llm: LLM instance for token counting

        Returns:
            Dict with token_count, threshold, percent_used, needs_compaction, warning
        """
        token_count = llm.count_message_tokens(messages)
        threshold_percent = (
            token_count / self.compaction_threshold_tokens
            if self.compaction_threshold_tokens > 0
            else 0
        )

        return {
            "token_count": token_count,
            "threshold": self.compaction_threshold_tokens,
            "percent_used": threshold_percent,
            "needs_compaction": threshold_percent >= 1.0,
            "warning": threshold_percent >= self.warning_threshold_percent,
            "message_count": len(messages),
        }

    async def compact_if_needed(
        self, messages: List["Message"], llm: "LLM"
    ) -> List["Message"]:
        """
        Apply compaction if context exceeds threshold.

        Args:
            messages: Current message list
            llm: LLM instance for token counting and summarization

        Returns:
            Possibly compacted message list
        """
        health = await self.check_context_health(messages, llm)

        # Log warning if approaching threshold
        if health["warning"] and not health["needs_compaction"]:
            logger.warning(
                f"Context at {health['percent_used']:.1%} of threshold "
                f"({health['token_count']:,}/{self.compaction_threshold_tokens:,} tokens, "
                f"{health['message_count']} messages)"
            )

        # Only compact if we've exceeded the threshold
        if not health["needs_compaction"]:
            return messages

        logger.info(
            f"Context exceeded threshold ({health['token_count']:,} tokens). "
            f"Applying {self.strategy} compaction..."
        )
        original_count = health["token_count"]

        # Apply the configured strategy
        if self.strategy == "simple":
            messages = await self.simple_strategy.apply(messages)
        elif self.strategy == "summarize":
            messages = await self._summarize_messages(messages, llm)
        elif self.strategy == "composite":
            for strat in self.composite_strategies:
                messages = await strat.apply(messages)

        # Recalculate and log results
        new_count = llm.count_message_tokens(messages)
        self.compaction_count += 1
        self.last_compaction_savings = original_count - new_count
        self.total_tokens_saved += self.last_compaction_savings

        reduction_percent = (
            (self.last_compaction_savings / original_count * 100)
            if original_count > 0
            else 0
        )
        logger.info(
            f"Compaction complete. Reduced {original_count:,} -> {new_count:,} tokens "
            f"({self.last_compaction_savings:,} saved, {reduction_percent:.1f}% reduction)"
        )

        return messages

    async def force_compact(
        self, messages: List["Message"], llm: "LLM"
    ) -> List["Message"]:
        """
        Force compaction regardless of threshold.
        Useful when you know context needs to be reduced.
        """
        original_count = llm.count_message_tokens(messages)

        if self.strategy == "simple":
            messages = await self.simple_strategy.apply(messages)
        elif self.strategy == "summarize":
            messages = await self._summarize_messages(messages, llm)
        elif self.strategy == "composite":
            for strat in self.composite_strategies:
                messages = await strat.apply(messages)

        new_count = llm.count_message_tokens(messages)
        self.compaction_count += 1
        self.last_compaction_savings = original_count - new_count
        self.total_tokens_saved += self.last_compaction_savings

        return messages

    async def _summarize_messages(
        self, messages: List["Message"], llm: "LLM"
    ) -> List["Message"]:
        """
        Generate summary and replace history.
        Works with any LLM provider.
        """
        from app.schema import Message

        summary_prompt = self.summarizer.get_summary_prompt()
        summary_request = Message.user_message(summary_prompt)

        try:
            # Generate summary using the LLM (works with any provider)
            response = await llm.ask(
                messages=messages + [summary_request],
                model=self.summarizer.summary_model,  # None = use default model
            )

            # Extract summary from <summary> tags
            summary_text = self._extract_summary(response)

            # Preserve system message if it exists
            system_content = ""
            if messages and messages[0].role == "system":
                system_content = messages[0].content or ""

            # Replace entire history with summary
            new_messages = []
            if system_content:
                new_messages.append(Message.system_message(system_content))

            new_messages.append(
                Message.user_message(
                    f"<summary>\n{summary_text}\n</summary>\n\n"
                    "Continue from this context. The above summary contains the key information "
                    "from our previous conversation."
                )
            )

            logger.info(
                f"Generated summary ({len(summary_text)} chars), replaced {len(messages)} messages"
            )
            return new_messages

        except Exception as e:
            logger.error(
                f"Failed to generate summary: {e}. Falling back to selective retention."
            )
            return await self.simple_strategy.apply(messages)

    def _extract_summary(self, response: str) -> str:
        """Extract content from <summary> tags"""
        match = re.search(r"<summary>(.*?)</summary>", response, re.DOTALL)
        if match:
            return match.group(1).strip()
        logger.warning("No <summary> tags found in response, using full response")
        return response.strip()

    def get_stats(self) -> Dict[str, Any]:
        """Get compaction statistics"""
        return {
            "compaction_count": self.compaction_count,
            "total_tokens_saved": self.total_tokens_saved,
            "last_compaction_savings": self.last_compaction_savings,
            "strategy": self.strategy,
            "threshold": self.compaction_threshold_tokens,
        }

    def reset_stats(self):
        """Reset compaction statistics"""
        self.compaction_count = 0
        self.total_tokens_saved = 0
        self.last_compaction_savings = 0
