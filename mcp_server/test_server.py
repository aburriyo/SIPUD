#!/usr/bin/env python3
"""Simple MCP server for testing"""

import asyncio
import sys

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types
from mcp.server.models import InitializationOptions

server = Server("test-server")

@server.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="test",
            description="A simple test tool",
            inputSchema={
                "type": "object",
                "properties": {
                    "message": {"type": "string"}
                },
            },
        )
    ]

@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    if name == "test":
        msg = arguments.get("message", "Hello from MCP!")
        return [types.TextContent(type="text", text=f"Test response: {msg}")]
    return [types.TextContent(type="text", text="Unknown tool")]

async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="test-server",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options={},
                    experimental_capabilities={},
                ),
            ),
        )

if __name__ == "__main__":
    asyncio.run(main())
