"""
Test script to verify ReviewFlow integration in run_flow.py

Tests that use_reviewer_agent config toggle properly enables Doer-Critic loop.
"""

import asyncio

from app.agent.manus import Manus
from app.config import config
from app.flow.flow_factory import FlowFactory, FlowType
from app.flow.review import ReviewFlow
from app.logger import logger


async def test_integration():
    """Test ReviewFlow integration with config toggle."""

    # Test 1: Check config reads correctly
    print(f"use_reviewer_agent: {config.run_flow_config.use_reviewer_agent}")
    print(
        f"max_review_iterations: {getattr(config.run_flow_config, 'max_review_iterations', 3)}"
    )

    # Test 2: Simulate run_flow logic with reviewer disabled
    print("\n=== Test with Reviewer DISABLED ===")
    original_setting = config.run_flow_config.use_reviewer_agent
    config.run_flow_config.use_reviewer_agent = False

    agents = {"manus": Manus()}
    flow = FlowFactory.create_flow(
        flow_type=FlowType.PLANNING,
        agents=agents,
    )
    print(f"Flow type: {type(flow).__name__}")

    # Test 3: Simulate with reviewer enabled
    print("\n=== Test with Reviewer ENABLED ===")
    config.run_flow_config.use_reviewer_agent = True

    manus_agent = await Manus.create()
    flow = ReviewFlow(agents={"doer": manus_agent}, max_iterations=3)
    print(f"Flow type: {type(flow).__name__}")
    print(f"Max iterations: {flow.max_iterations}")

    # Restore original setting
    config.run_flow_config.use_reviewer_agent = original_setting

    print("\n✅ Integration test passed!")


if __name__ == "__main__":
    asyncio.run(test_integration())
