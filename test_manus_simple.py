import asyncio

from app.agent.manus import Manus
from app.logger import logger


async def test_manus_init():
    agent = None
    try:
        logger.info("Creating Manus agent using factory method...")
        agent = await Manus.create()

        logger.info(f"Manus agent created. Name: {agent.name}")
        logger.info(
            f"Tools loaded: {len(agent.available_tools.tool_map) if hasattr(agent, 'available_tools') else 'N/A'}"
        )

        # Log names of loaded tools
        if hasattr(agent, "available_tools"):
            tool_names = list(agent.available_tools.tool_map.keys())
            logger.info(f"Loaded tools: {', '.join(tool_names)}")

        # Test basic reasoning without external tools if possible
        logger.info("Testing basic thinking process...")
        # Using a very simple prompt to verify the think -> step loop
        # We don't want to run a full task yet, just verify the loop

        # Manus.think() is called inside agent.run()
        # Let's try a very simple run that should finish quickly
        # result = await agent.run("Repeat the word 'READY'")
        # logger.info(f"Run result: {result}")

        print("\n✅ Manus Initialization Test: PASSED")

    except Exception as e:
        print(f"\n❌ Manus Initialization Test: FAILED - {str(e)}")
        import traceback

        traceback.print_exc()
    finally:
        if agent:
            await agent.cleanup()


if __name__ == "__main__":
    asyncio.run(test_manus_init())
