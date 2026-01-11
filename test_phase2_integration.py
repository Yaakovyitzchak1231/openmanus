"""
Phase 2 End-to-End Integration Test

Tests all Phase 2 features together:
- ReviewFlow with Doer-Critic loop
- Enhanced decomposition (5-10 steps)
- Verification loops (3-retry)
- Cost tracking
"""

import asyncio

from app.agent.manus import Manus
from app.flow.review import ReviewFlow


async def test_phase2_integration():
    """Run comprehensive Phase 2 integration test."""

    print("=" * 80)
    print("PHASE 2 INTEGRATION TEST")
    print("=" * 80)

    # Create Manus agent as doer
    print("\n1. Creating Manus agent...")
    doer = await Manus.create()
    print(f"   ✓ Doer created: {doer.name}")
    print(f"   ✓ Max steps: {doer.max_steps}")
    print(f"   ✓ Effort level: {doer.effort_level}")

    # Create ReviewFlow
    print("\n2. Creating ReviewFlow...")
    flow = ReviewFlow(agents={"doer": doer}, max_iterations=3)
    print(f"   ✓ ReviewFlow created")
    print(f"   ✓ Max review iterations: {flow.max_iterations}")

    # Test task: Create a simple web scraper with proper error handling
    task = """Create a Python web scraper that:
1. Fetches the title from https://example.com
2. Handles network errors gracefully
3. Has a timeout of 5 seconds
4. Returns the title or an error message
5. Include basic unit tests

Make sure the code is clean, well-documented, and follows best practices."""

    print("\n3. Running test task...")
    print(f"   Task: {task[:100]}...")

    try:
        result = await flow.execute(task)

        print("\n" + "=" * 80)
        print("TEST RESULT:")
        print("=" * 80)
        print(result)
        print("=" * 80)

        # Check if review iterations occurred
        if "iteration" in result.lower():
            print("\n✅ SUCCESS: Doer-Critic iterations detected")
        else:
            print("\n⚠️ WARNING: No iteration information in result")

        # Check for PASS/FAIL grade
        if "PASS" in result or "FAIL" in result:
            print("✅ SUCCESS: Reviewer grading detected")
        else:
            print("⚠️ WARNING: No reviewer grade found")

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        raise

    print("\n" + "=" * 80)
    print("PHASE 2 TEST COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(test_phase2_integration())
