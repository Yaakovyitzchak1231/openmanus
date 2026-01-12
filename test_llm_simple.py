import asyncio

from app.llm import LLM
from app.logger import logger


async def test_llm():
    try:
        logger.info("Initializing LLM...")
        llm = LLM()
        logger.info(f"Testing model: {llm.model}")

        prompt = [
            {"role": "user", "content": "Hello, respond with exactly One word: SUCCESS"}
        ]
        logger.info(f"Sending prompt: {prompt}")

        # Test basic ask
        response = await llm.ask(prompt)
        logger.info(f"LLM Response: {response}")

        if "SUCCESS" in response.upper():
            print("\n✅ LLM Communication Test: PASSED")
        else:
            print(
                f"\n❌ LLM Communication Test: FAILED (Unexpected response: {response})"
            )

    except Exception as e:
        print(f"\n❌ LLM Communication Test: ERROR - {str(e)}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_llm())
