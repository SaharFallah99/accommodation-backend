import asyncio
import json
from collections import Counter

from mcp import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client

CITIES = ["رامسر", "شیراز", "اصفهان", "کیش"]
CHECK_IN = "2026-11-26"
CHECK_OUT = "2026-11-29"


async def call(session, name, args):
    result = await session.call_tool(name, args)
    for block in result.content:
        if getattr(block, "type", None) == "text":
            return json.loads(block.text)
    raise RuntimeError(f"No text result for {name}")


async def main() -> None:
    params = StdioServerParameters(command="uvx", args=["jabama-mcp"])
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            for city in CITIES:
                dest = await call(session, "jb_find_destination", {"query": city})
                city_match = next((d for d in dest["destinations"] if d["kind"] == "city"), None)
                print("CITY", city, city_match)
                if not city_match:
                    continue
                search = await call(
                    session,
                    "jb_search_stays",
                    {
                        **city_match["search"],
                        "check_in": CHECK_IN,
                        "check_out": CHECK_OUT,
                        "guests": 2,
                        "limit": 20,
                    },
                )
                stays = search.get("stays") or []
                print(
                    "  total",
                    search.get("total"),
                    "returned",
                    len(stays),
                    "types",
                    Counter(s.get("type") for s in stays),
                )
                for s in stays[:5]:
                    print(
                        "   ",
                        s.get("code"),
                        s.get("type"),
                        s.get("title"),
                        s.get("city"),
                        s.get("rating"),
                        s.get("rating_count"),
                        s.get("cheapest_night"),
                        s.get("total_price"),
                        "img" if s.get("image") else "no-img",
                    )
                await asyncio.sleep(0.8)


if __name__ == "__main__":
    asyncio.run(main())
