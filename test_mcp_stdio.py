"""
Direct test of MCP stdio connection
"""

import asyncio
from contextlib import AsyncExitStack

from mcp import StdioServerParameters
from mcp.client.stdio import stdio_client


async def test_stdio_connection():
    print("Testing MCP stdio connection directly...")

    params = StdioServerParameters(
        command="npx",
        args=[
            "-y",
            "@modelcontextprotocol/server-filesystem",
            "c:/Users/jacob/Desktop",
        ],
    )

    print(f"Command: {params.command}")
    print(f"Args: {params.args}")

    try:
        exit_stack = AsyncExitStack()
        await exit_stack.enter_async_context(stdio_client(params))
        print("✅ Connection successful!")
        await exit_stack.aclose()
    except FileNotFoundError as e:
        print(f"❌ FileNotFoundError: {e}")
        print("npx command not found in PATH")
    except Exception as e:
        print(f"❌ Error: {type(e).__name__}: {e}")


if __name__ == "__main__":
    asyncio.run(test_stdio_connection())
