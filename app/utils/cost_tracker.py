"""
Cost Tracker for OpenManus - Phase 1.5
Monitors API token usage and costs with OpenRouter pricing.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

from app.logger import logger


# OpenRouter pricing (per 1M tokens) - updated as of Jan 2025
OPENROUTER_PRICING = {
    "openai/gpt-4o-mini": {"input": 0.15, "output": 0.60},
    "anthropic/claude-3.5-sonnet": {"input": 3.00, "output": 15.00},
    "anthropic/claude-3-7-sonnet-20250219": {"input": 3.00, "output": 15.00},
    "meta-llama/llama-3.3-70b-instruct": {"input": 0.35, "output": 0.40},
    "deepseek/deepseek-chat": {"input": 0.14, "output": 0.28},
    "deepseek/deepseek-coder": {"input": 0.14, "output": 0.28},
    "codellama/codellama-70b-instruct": {"input": 0.78, "output": 0.78},
    "openai/gpt-4o": {"input": 2.50, "output": 10.00},
}


class CostTracker:
    """Track API costs and token usage with OpenRouter pricing."""

    def __init__(self, log_file: str = "costs.json", budget_limit: float = 20.0):
        """
        Initialize cost tracker.

        Args:
            log_file: Path to JSON file for cost logging
            budget_limit: Total budget limit in USD (informational only, no hard limits)
        """
        self.log_file = Path(log_file)
        self.budget_limit = budget_limit
        self.warn_thresholds = [10.0, 15.0, 18.0]  # Warning points
        self._warned_thresholds = set()  # Track which warnings were shown

        # Initialize log file if doesn't exist
        if not self.log_file.exists():
            self.log_file.write_text(json.dumps([], indent=2))

    def log_api_call(
        self,
        model: str,
        input_tokens: int,
        output_tokens: int,
        prompt: Optional[str] = None,
        response: Optional[str] = None,
    ) -> float:
        """
        Log an API call and return estimated cost.

        Args:
            model: Model name (e.g., "openai/gpt-4o-mini")
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            prompt: Optional prompt text (truncated if >500 chars)
            response: Optional response text (truncated if >500 chars)

        Returns:
            Estimated cost for this call in USD
        """
        # Calculate cost
        cost = self._calculate_cost(model, input_tokens, output_tokens)

        # Create log entry
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "model": model,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": input_tokens + output_tokens,
            "estimated_cost_usd": round(cost, 4),
            "prompt_preview": (
                prompt[:500] + "..." if prompt and len(prompt) > 500 else prompt
            ),
            "response_preview": (
                response[:500] + "..." if response and len(response) > 500 else response
            ),
        }

        # Append to log file
        logs = self._read_logs()
        logs.append(entry)
        self.log_file.write_text(json.dumps(logs, indent=2))

        # Check total spend and warn if needed
        total_spend = self.get_total_spend()
        self._check_warnings(total_spend)

        logger.info(
            f"API call logged: {model} | {input_tokens}in + {output_tokens}out = ${cost:.4f} | Total: ${total_spend:.2f}/${self.budget_limit}"
        )

        return cost

    def _calculate_cost(
        self, model: str, input_tokens: int, output_tokens: int
    ) -> float:
        """Calculate cost based on OpenRouter pricing."""
        if model not in OPENROUTER_PRICING:
            logger.warning(
                f"Model {model} not in pricing table. Using GPT-4o-mini pricing as fallback."
            )
            pricing = OPENROUTER_PRICING["openai/gpt-4o-mini"]
        else:
            pricing = OPENROUTER_PRICING[model]

        input_cost = (input_tokens / 1_000_000) * pricing["input"]
        output_cost = (output_tokens / 1_000_000) * pricing["output"]

        return input_cost + output_cost

    def _read_logs(self) -> list:
        """Read existing logs from file."""
        if not self.log_file.exists():
            return []
        return json.loads(self.log_file.read_text())

    def get_total_spend(self) -> float:
        """Get total spend across all logged API calls."""
        logs = self._read_logs()
        return sum(entry.get("estimated_cost_usd", 0) for entry in logs)

    def _check_warnings(self, total_spend: float):
        """Check if we've crossed warning thresholds."""
        for threshold in self.warn_thresholds:
            if total_spend >= threshold and threshold not in self._warned_thresholds:
                self._warned_thresholds.add(threshold)
                percentage = (total_spend / self.budget_limit) * 100

                if threshold == 10.0:
                    logger.warning(
                        f"💰 Budget Alert: Halfway through budget (${total_spend:.2f}/${self.budget_limit})"
                    )
                elif threshold == 15.0:
                    logger.warning(
                        f"💰 Budget Alert: Approaching budget limit (${total_spend:.2f}/${self.budget_limit} - {percentage:.1f}%)"
                    )
                elif threshold == 18.0:
                    logger.warning(
                        f"💰 Budget Alert: Budget nearly exhausted (${total_spend:.2f}/${self.budget_limit} - {percentage:.1f}%). Consider using cloud GPU for RL training."
                    )

    def get_stats(self) -> Dict:
        """Get summary statistics."""
        logs = self._read_logs()
        if not logs:
            return {"total_calls": 0, "total_spend": 0.0, "models_used": []}

        model_usage = {}
        for entry in logs:
            model = entry.get("model", "unknown")
            if model not in model_usage:
                model_usage[model] = {
                    "calls": 0,
                    "input_tokens": 0,
                    "output_tokens": 0,
                    "cost": 0.0,
                }
            model_usage[model]["calls"] += 1
            model_usage[model]["input_tokens"] += entry.get("input_tokens", 0)
            model_usage[model]["output_tokens"] += entry.get("output_tokens", 0)
            model_usage[model]["cost"] += entry.get("estimated_cost_usd", 0)

        return {
            "total_calls": len(logs),
            "total_spend": self.get_total_spend(),
            "budget_limit": self.budget_limit,
            "budget_remaining": self.budget_limit - self.get_total_spend(),
            "budget_used_percent": (self.get_total_spend() / self.budget_limit) * 100,
            "models_used": model_usage,
        }


# Global tracker instance
_tracker: Optional[CostTracker] = None


def get_tracker() -> CostTracker:
    """Get or create global cost tracker instance."""
    global _tracker
    if _tracker is None:
        _tracker = CostTracker()
    return _tracker
