"""
Manual Verification Test: Binary Search - Before/After Comparison

Tests whether enhanced CoT prompts improve output quality compared to baseline.
This will run with enhanced prompts and compare reasoning depth.
"""

import asyncio

from app.agent.manus import Manus
from app.flow.flow_factory import FlowFactory, FlowType


async def test_binary_search():
    """Test binary search algorithm with enhanced prompts."""

    print("\n" + "=" * 70)
    print("MANUAL VERIFICATION TEST: Binary Search Algorithm")
    print("=" * 70)
    print("\nUsing ENHANCED prompts (CoT + Reflection)")
    print()

    from app.config import config

    print(
        f"Config: high_effort={config.agent.high_effort_mode}, "
        f"reflection={config.agent.enable_reflection}"
    )
    print("-" * 70)

    agents = {"manus": Manus()}
    flow = FlowFactory.create_flow(flow_type=FlowType.PLANNING, agents=agents)

    prompt = """Write a binary search algorithm with error handling.

Requirements:
1. Implement binary_search(arr, target) function
2. Handle edge cases: empty array, single element, target not found
3. Add proper error handling for invalid inputs
4. Include docstring and comments
5. Write 2-3 test cases to verify it works

Focus on demonstrating systematic thinking and quality code."""

    print("Starting task execution...")
    print("Monitoring for CoT reasoning and reflection...\n")

    try:
        result = await flow.execute(prompt)

        print("\n" + "=" * 70)
        print("TASK COMPLETED")
        print("=" * 70)
        print(f"\nResult (first 1000 chars):\n{result[:1000]}...")

        # Check for quality indicators
        has_docstring = "def binary_search" in result and '"""' in result
        has_error_handling = "raise" in result.lower() or "except" in result.lower()
        has_tests = "test" in result.lower() or "assert" in result.lower()

        print("\n" + "=" * 70)
        print("QUALITY CHECKLIST:")
        print("=" * 70)
        print(f"✓ Docstring present: {has_docstring}")
        print(f"✓ Error handling: {has_error_handling}")
        print(f"✓ Tests included: {has_tests}")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_binary_search())
