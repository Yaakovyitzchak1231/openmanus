import sys

from app.logger import logger
from app.tool import (
    Bash,
    BrowserUseTool,
    Crawl4aiTool,
    PlanningTool,
    PythonExecute,
    StrReplaceEditor,
    TestRunner,
    WebSearch,
)


def test_tool_imports():
    tools_to_test = [
        ("Bash", Bash),
        ("BrowserUseTool", BrowserUseTool),
        ("StrReplaceEditor", StrReplaceEditor),
        ("PythonExecute", PythonExecute),
        ("TestRunner", TestRunner),
        ("WebSearch", WebSearch),
        ("PlanningTool", PlanningTool),
        ("Crawl4aiTool", Crawl4aiTool),
    ]

    failed = []
    for name, tool_class in tools_to_test:
        try:
            logger.info(f"Initializing {name}...")
            tool_class()
            logger.info(f"✅ {name} initialized successfully.")
        except Exception as e:
            logger.error(f"❌ {name} failed: {str(e)}")
            failed.append(name)

    if not failed:
        print("\n✅ All Tool Imports: PASSED")
    else:
        print(f"\n❌ Tool Import Failures: {', '.join(failed)}")
        sys.exit(1)


if __name__ == "__main__":
    test_tool_imports()
