import asyncio
import json

from mcp import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client


async def main() -> None:
    params = StdioServerParameters(command="uvx", args=["jabama-mcp"])
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()
            print("TOOLS:", [t.name for t in tools.tools])
            result = await session.call_tool("jb_find_destination", {"query": "رامسر"})
            for block in result.content:
                if getattr(block, "type", None) == "text":
                    data = json.loads(block.text)
                    print("FIRST:", json.dumps(data["destinations"][0], ensure_ascii=False))


if __name__ == "__main__":
    asyncio.run(main())
