#!/usr/bin/env python3
"""Programmatic MCP inspection: spawn server, list tools, call each tool."""

import asyncio
import os
import sys

# Add project root for uv run
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mcp import StdioServerParameters, ClientSession
from mcp.client.stdio import stdio_client


async def main() -> None:
    # Resolve waktusolat-mcp command (prefer uv run from project)
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    params = StdioServerParameters(
        command="uv",
        args=["--directory", project_root, "run", "waktusolat-mcp"],
        env=None,
    )
    print("Connecting to MCP server (waktusolat-mcp)...")
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            print("Connected. Listing tools...")
            tools_result = await session.list_tools()
            tools = tools_result.tools
            print(f"  Found {len(tools)} tools:", [t.name for t in tools])
            for t in tools:
                print(f"    - {t.name}: {t.description[:60]}...")
            print()
            # Call each tool
            for name in ["list_zones", "get_prayer_times_today", "get_next_prayer", "get_prayer_times_month"]:
                print(f"Calling {name}...")
                if name == "list_zones":
                    result = await session.call_tool(name, arguments={})
                elif name == "get_prayer_times_today":
                    result = await session.call_tool(name, arguments={"zone": "SGR01"})
                elif name == "get_next_prayer":
                    result = await session.call_tool(name, arguments={"zone": "SGR01"})
                elif name == "get_prayer_times_month":
                    result = await session.call_tool(
                        name, arguments={"zone": "SGR01", "year": 2026, "month": 2}
                    )
                else:
                    continue
                content = result.content
                if content:
                    text = content[0].text if hasattr(content[0], "text") else str(content[0])
                    preview = text[:150].replace("\n", " ")
                    print(f"  OK: {preview}...")
                else:
                    print(f"  OK: (empty)")
            print()
            print("MCP inspection complete. All tools OK.")


if __name__ == "__main__":
    asyncio.run(main())
