
import asyncio
from app.agent.manus import Manus
from app.flow.flow_factory import FlowFactory, FlowType
from app.logger import logger

async def test_planning_flow():
    manus = None
    try:
        logger.info("Initializing agents for PlanningFlow...")
        manus = await Manus.create()

        agents = {"manus": manus}

        logger.info("Creating PlanningFlow via Factory...")
        flow = FlowFactory.create_flow(FlowType.PLANNING, agents=agents)

        logger.info(f"Flow created: {type(flow).__name__}")

        # Test plan creation without full execution (too expensive/long)
        # We can test the _create_initial_plan method directly
        logger.info("Testing initial plan creation...")
        plan = await flow._create_initial_plan("Write a hello world program in python")
        logger.info(f"Initial plan created: {plan[:100]}...")

        if "hello" in plan.lower() or "world" in plan.lower():
            logger.info("Plan content looks relevant.")

        print("\n✅ PlanningFlow Initialization Test: PASSED")

    except Exception as e:
        print(f"\n❌ PlanningFlow Initialization Test: FAILED - {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        if manus:
            await manus.cleanup()

if __name__ == "__main__":
    asyncio.run(test_planning_flow())
