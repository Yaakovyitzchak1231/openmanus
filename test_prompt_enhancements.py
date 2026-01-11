"""
Test enhanced Chain-of-Thought prompts and self-reflection features.

Validates that:
1. Enhanced Manus prompt includes CoT instructions
2. Enhanced Reviewer prompt includes systematic analysis framework
3. Self-reflection is injected every 5 steps when enabled
"""

import asyncio

from app.agent.manus import Manus
from app.config import config
from app.prompt.manus import NEXT_STEP_PROMPT, SYSTEM_PROMPT


def test_manus_prompt_has_cot():
    """Verify Manus system prompt includes Chain-of-Thought instructions."""
    assert (
        "Chain-of-Thought" in SYSTEM_PROMPT
    ), "Manus prompt should mention Chain-of-Thought"
    assert (
        "Reasoning Framework" in SYSTEM_PROMPT
    ), "Manus prompt should have reasoning framework"
    assert "Understand" in SYSTEM_PROMPT, "Manus prompt should have 'Understand' step"
    assert "Analyze" in SYSTEM_PROMPT, "Manus prompt should have 'Analyze' step"
    assert "Plan" in SYSTEM_PROMPT, "Manus prompt should have 'Plan' step"
    assert "Execute" in SYSTEM_PROMPT, "Manus prompt should have 'Execute' step"
    assert "Verify" in SYSTEM_PROMPT, "Manus prompt should have 'Verify' step"
    print("✅ Manus prompt has CoT framework")


def test_manus_next_step_has_decision_process():
    """Verify Manus next step prompt includes decision process."""
    assert "Next Step Decision Process" in NEXT_STEP_PROMPT
    assert "Assess Current State" in NEXT_STEP_PROMPT
    assert "Identify Next Action" in NEXT_STEP_PROMPT
    assert "Select Tools" in NEXT_STEP_PROMPT
    print("✅ Manus next_step prompt has decision framework")


def test_reviewer_prompt_has_cot():
    """Verify Reviewer prompt includes CoT analysis framework."""
    from app.agent.reviewer import REVIEWER_SYSTEM_PROMPT

    assert "Chain-of-Thought" in REVIEWER_SYSTEM_PROMPT
    assert "BEFORE grading, systematically analyze" in REVIEWER_SYSTEM_PROMPT
    assert "Logic & Correctness" in REVIEWER_SYSTEM_PROMPT
    assert "Error Handling & Robustness" in REVIEWER_SYSTEM_PROMPT
    assert "Security & Safety" in REVIEWER_SYSTEM_PROMPT
    assert "THINK STEP-BY-STEP" in REVIEWER_SYSTEM_PROMPT
    print("✅ Reviewer prompt has CoT analysis framework")


async def test_reflection_injection():
    """Test that reflection prompts are injected every 5 steps."""
    # Enable reflection
    original_reflection = getattr(config.agent, "enable_reflection", False)
    original_high_effort = getattr(config.agent, "high_effort_mode", False)

    config.agent.enable_reflection = True
    config.agent.high_effort_mode = True

    manus = await Manus.create()

    # Simulate being at step 5
    manus.current_step = 5

    initial_message_count = len(manus.memory.messages)

    # Call think() which should inject reflection
    try:
        # We don't actually want it to execute fully, just check injection
        # Note: This will fail because there's no prompt, but that's ok - we're testing injection
        await manus.think()
    except Exception:
        # Expected to fail, we just want to check if reflection was injected
        pass

    # Check if reflection was added
    final_message_count = len(manus.memory.messages)

    # Should have at least one more message (the reflection)
    assert (
        final_message_count > initial_message_count
    ), "Reflection should be injected at step 5"

    # Check if any message contains reflection checkpoint
    has_reflection = any(
        "Reflection Checkpoint" in str(msg.content)
        for msg in manus.memory.messages
        if msg.content
    )
    assert has_reflection, "Memory should contain reflection checkpoint message"

    # Restore settings
    config.agent.enable_reflection = original_reflection
    config.agent.high_effort_mode = original_high_effort

    await manus.cleanup()
    print("✅ Self-reflection injection works at step 5")


async def main():
    """Run all prompt enhancement tests."""
    print("\n=== Testing Phase 3 Prompt Enhancements ===\n")

    test_manus_prompt_has_cot()
    test_manus_next_step_has_decision_process()
    test_reviewer_prompt_has_cot()
    await test_reflection_injection()

    print("\n✅ All prompt enhancement tests PASSED!\n")


if __name__ == "__main__":
    asyncio.run(main())
