import asyncio
import time

from app.agent.data_analysis import DataAnalysis
from app.agent.manus import Manus
from app.config import config
from app.flow.flow_factory import FlowFactory, FlowType
from app.flow.review import ReviewFlow
from app.logger import logger


async def run_flow():
    # Initialize agents asynchronously to ensure MCP servers connect properly
    agents = {
        "manus": await Manus.create(),  # Use async factory method for proper MCP initialization
    }
    if config.run_flow_config.use_data_analysis_agent:
        agents["data_analysis"] = await DataAnalysis.create()

    try:
        prompt = input("Enter your prompt: ")

        if prompt.strip().isspace() or not prompt:
            logger.warning("Empty prompt provided.")
            return

        # Create base flow (PlanningFlow)
        flow = FlowFactory.create_flow(
            flow_type=FlowType.PLANNING,
            agents=agents,
        )

        # Phase 2: Wrap with ReviewFlow if use_reviewer_agent is enabled
        if config.run_flow_config.use_reviewer_agent:
            logger.info(
                "Reviewer agent enabled - using Doer-Critic self-correction loop"
            )
            max_iterations = getattr(config.run_flow_config, "max_review_iterations", 3)

            # Use Manus as the doer agent for ReviewFlow
            manus_agent = await Manus.create()
            flow = ReviewFlow(
                agents={"doer": manus_agent}, max_iterations=max_iterations
            )

        logger.warning("Processing your request...")

        try:
            start_time = time.time()
            result = await asyncio.wait_for(
                flow.execute(prompt),
                timeout=3600,  # 60 minute timeout for the entire execution
            )
            elapsed_time = time.time() - start_time
            logger.info(f"Request processed in {elapsed_time:.2f} seconds")
            logger.info(result)
        except asyncio.TimeoutError:
            logger.error("Request processing timed out after 1 hour")
            logger.info(
                "Operation terminated due to timeout. Please try a simpler request."
            )

    except KeyboardInterrupt:
        logger.info("Operation cancelled by user.")
    except Exception as e:
        logger.error(f"Error: {str(e)}")


if __name__ == "__main__":
    asyncio.run(run_flow())
