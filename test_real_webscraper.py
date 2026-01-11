"""
Real integration test for Phase 3 prompt enhancements.

Tests the web scraper scenario with high-effort mode and reflection enabled.
Will be monitored and killed once reflection is confirmed working.
"""

import asyncio

from app.agent.manus import Manus
from app.flow.flow_factory import FlowFactory, FlowType


async def test_webscraper_with_reflection():
    """Run a simplified web scraper task to test reflection mechanism."""

    print("\n" + "=" * 70)
    print("REAL INTEGRATION TEST: Web Scraper with Reflection")
    print("=" * 70)
    print("\nConfig Check:")
    from app.config import config

    print(f"  high_effort_mode: {config.agent.high_effort_mode}")
    print(f"  enable_reflection: {config.agent.enable_reflection}")
    print(f"  max_steps: {config.agent.max_steps_high_effort}")
    print()

    # Create agent
    agents = {"manus": Manus()}

    # Create flow
    flow = FlowFactory.create_flow(
        flow_type=FlowType.PLANNING,
        agents=agents,
    )

    # Simplified prompt to reduce token usage while still testing reflection
    prompt = """Write a Python function to fetch the top 5 Hacker News posts.

Requirements:
1. Use requests library to fetch from HN API
2. Parse JSON response
3. Extract title and URL for each post
4. Return as a list of dictionaries
5. Include basic error handling

Focus on completing this efficiently to demonstrate the reflection mechanism."""

    print("Starting task execution...")
    print("Will monitor for reflection prompts at steps 5, 10, 15, etc.")
    print("-" * 70)

    try:
        result = await flow.execute(prompt)
        print("\n" + "=" * 70)
        print("TASK COMPLETED")
        print("=" * 70)
        print(f"\nResult summary (first 500 chars):\n{result[:500]}...")

    except Exception as e:
        print(f"\n❌ Error during execution: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_webscraper_with_reflection())
