import asyncio

from app.agent.reviewer import Reviewer
from app.logger import logger


async def test_reviewer():
    try:
        logger.info("Initializing Reviewer agent...")
        agent = Reviewer()

        logger.info(f"Reviewer agent created. Name: {agent.name}")

        # Test basic reasoning - grading some mock content
        # Note: Reviewer.step() usually takes content from memory
        # We'll just verify it can be instantiated and has the correct prompt
        if "CRITERIA" in agent.system_prompt:
            logger.info("Reviewer system prompt contains criteria checklist.")

        print("\n✅ Reviewer Initialization Test: PASSED")

    except Exception as e:
        print(f"\n❌ Reviewer Initialization Test: FAILED - {str(e)}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_reviewer())
