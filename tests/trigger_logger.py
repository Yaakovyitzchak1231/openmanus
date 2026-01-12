import asyncio

from app.tool.feedback_logger import FeedbackLogger


async def test():
    logger = FeedbackLogger()
    result = await logger.execute(
        step_text="Test verification step",
        agent_name="ManusTest",
        user_feedback="This is a manual verification log entry.",
        successful_correction=True,
    )
    print(result)


if __name__ == "__main__":
    asyncio.run(test())
