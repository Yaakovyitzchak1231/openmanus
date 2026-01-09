"""
Simple test script to verify ReviewFlow works with Doer-Critic iteration.
"""

import asyncio

from app.agent.manus import Manus
from app.flow.review import ReviewFlow


async def test_review_flow():
    """Test ReviewFlow with a simple buggy code task."""
    # Create Manus agent as doer
    doer = await Manus.create()

    # Create ReviewFlow
    flow = ReviewFlow(agents={"doer": doer}, max_iterations=3)

    # Test with intentionally buggy task
    task = """Write a Python function to calculate the factorial of a number.
    Make sure to handle edge cases like n=0 and negative numbers."""

    print("Testing ReviewFlow...")
    print(f"Task: {task}\n")

    result = await flow.run(task)

    print("\n" + "=" * 80)
    print("FINAL RESULT:")
    print("=" * 80)
    print(result)

    return result


if __name__ == "__main__":
    asyncio.run(test_review_flow())
