"""Convenience script to look up all the tools on an MCP server and print a sketch of a FastMCP server that looks the same."""
import asyncio
from typing import Any

from fastmcp import Client

client = Client("http://127.0.0.1:64342/stream")


async def main():
    async with client:
        # List available operations
        tools = await client.list_tools()
        # resources = await client.list_resources()
        # prompts = await client.list_prompts()

        for tool in tools:
            property: dict[str, Any]

            print("@mcp.tool")
            print(f"def {tool.name} (")
            for prop_name, prop in tool.input_schema["properties"].items():
                description = prop["description"].replace("\n", "\\n")
                print(f'    {prop_name}: Annotated[{prop["type"]}, "{description}"],  # {prop}')
            print(f') -> dict[str, Any]:  # {tool.output_schema}')
            print(f'    """{tool.description}"""')
            print("    pass")
            print()
            print()


asyncio.run(main())
