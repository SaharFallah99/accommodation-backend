"""Collect a static Jabama stay catalogue through the jabama-mcp MCP server.

The frontend reads the generated JSON at build time; it never calls MCP.
"""

from __future__ import annotations

import asyncio
import json
import math
import re
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from mcp import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
CACHE_DIR = DATA_DIR / "jabama_cache"
RAW_PATH = DATA_DIR / "jabama_raw.json"
OUT_PATH = DATA_DIR / "stays.json"
PLACEHOLDER = "/images/stay-placeholder.svg"

CHECK_IN = "2026-11-26"
CHECK_OUT = "2026-11-29"
ALT_CHECK_IN = "2026-12-03"
ALT_CHECK_OUT = "2026-12-06"
GUESTS = 2
PER_CITY = 10
CITIES = [
    {"name": "رامسر", "key": "ramsar"},
    {"name": "شیراز", "key": "shiraz"},
    {"name": "اصفهان", "key": "isfahan"},
    {"name": "کیش", "key": "kish"},
]
REVIEW_LIMIT = 5
SIMILAR_LIMIT = 6

SEM = asyncio.Semaphore(2)
RAW: dict[str, Any] = {}


def slugify(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-")


async def mcp_call(session: ClientSession, name: str, args: dict[str, Any], cache_key: str | None = None) -> Any:
    """Call one MCP tool, with an on-disk cache and at most two concurrent requests."""
    if cache_key:
        cached = CACHE_DIR / f"{cache_key}.json"
        if cached.exists():
            return json.loads(cached.read_text(encoding="utf-8"))

    async with SEM:
        await asyncio.sleep(0.7)  # be polite: space request starts
        result = await session.call_tool(name, args)

    texts = [getattr(block, "text", None) for block in result.content if getattr(block, "type", None) == "text"]
    if getattr(result, "isError", False):
        raise RuntimeError(f"{name} failed: {texts[0] if texts else 'unknown MCP error'}")
    if not texts:
        raise RuntimeError(f"{name} returned no text content")
    data = json.loads(texts[0])
    if cache_key:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        (CACHE_DIR / f"{cache_key}.json").write_text(
            json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
        )
    return data


def score(stay: dict[str, Any]) -> float:
    rating = stay.get("rating") or 0
    count = stay.get("rating_count") or 0
    return rating + 0.35 * math.log10(1 + count)


def choose_stays(stays: list[dict[str, Any]], limit: int) -> list[dict[str, Any]]:
    """Keep a type-diverse, well-rated sample instead of only the first page order."""
    unique: dict[int, dict[str, Any]] = {}
    for stay in stays:
        code = stay.get("code")
        if code and code not in unique:
            unique[code] = stay
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for stay in unique.values():
        grouped[str(stay.get("type") or "other")].append(stay)

    picked: list[dict[str, Any]] = []
    for group in sorted(grouped.values(), key=lambda items: -max(score(s) for s in items)):
        picked.append(max(group, key=score))
    rest = sorted((s for s in unique.values() if s not in picked), key=score, reverse=True)
    picked.extend(rest)
    return picked[:limit]


def beds_text(beds: dict[str, Any] | None) -> str:
    if not beds:
        return ""
    labels = {
        "single": "تخت یک‌نفره",
        "double": "تخت دونفره",
        "queen": "تخت کوئین",
        "king": "تخت کینگ",
        "sofa": "مبل تخت‌شو",
        "bunk": "تخت bunk",
    }
    parts = []
    for key, count in beds.items():
        if count:
            parts.append(f"{count} {labels.get(key, key)}")
    return "، ".join(parts)


def normalize_stay(
    card: dict[str, Any],
    detail: dict[str, Any],
    quote: dict[str, Any] | None,
    quote_dates: tuple[str, str] | None,
    quote_error: str | None,
    reviews: dict[str, Any] | None,
    similar: dict[str, Any] | None,
) -> dict[str, Any]:
    images: list[str] = []
    for url in [*(detail.get("images") or []), card.get("image")]:
        if url and url not in images:
            images.append(url)
    placeholder = not images
    if placeholder:
        images = [PLACEHOLDER]

    review_items = []
    for review in (reviews or {}).get("reviews") or []:
        review_items.append(
            {
                "rating": review.get("rating"),
                "text": review.get("text"),
                "author": review.get("author"),
                "stayed": review.get("stayed"),
                "stay_length": review.get("stay_length"),
                "host_reply": review.get("host_reply"),
            }
        )

    similar_items = []
    for item in (similar or {}).get("similar") or []:
        similar_items.append(
            {
                "code": item.get("code"),
                "title": item.get("title"),
                "type": item.get("type"),
                "city": item.get("city"),
                "province": item.get("province"),
                "rating": item.get("rating"),
                "rating_count": item.get("rating_count"),
                "max_guests": item.get("max_guests"),
                "total_price": item.get("total_price"),
                "cheapest_night": item.get("cheapest_night"),
                "image": item.get("image"),
                "url": item.get("url"),
            }
        )

    quote_block = None
    if quote:
        quote_block = {
            "check_in": quote.get("check_in"),
            "check_out": quote.get("check_out"),
            "nights": quote.get("nights"),
            "guests": quote.get("guests"),
            "payable": quote.get("payable"),
            "price_before_discount": quote.get("price_before_discount"),
            "discount": quote.get("discount"),
            "discount_pct": quote.get("discount_pct"),
            "instant_booking": quote.get("instant_booking"),
            "per_night": quote.get("per_night") or [],
            "cancellation": quote.get("cancellation"),
        }

    return {
        "code": detail.get("code") or card.get("code"),
        "title": detail.get("title") or card.get("title"),
        "type": detail.get("type") or card.get("type"),
        "city": detail.get("city") or card.get("city"),
        "province": detail.get("province") or card.get("province"),
        "region": card.get("region"),
        "area": None,
        "approx_location": detail.get("approx_location"),
        "url": detail.get("url") or card.get("url"),
        "active": detail.get("active"),
        "instant_booking": detail.get("instant_booking", card.get("instant_booking")),
        "capacity": {
            "base_guests": detail.get("base_guests") or card.get("base_guests"),
            "max_guests": detail.get("max_guests") or card.get("max_guests"),
        },
        "bedrooms": detail.get("bedrooms"),
        "beds": detail.get("beds") or {},
        "beds_text": beds_text(detail.get("beds")),
        "bathrooms": detail.get("bathrooms"),
        "area_m2": detail.get("area_m2"),
        "building_m2": detail.get("building_m2"),
        "check_in_time": detail.get("check_in_time"),
        "check_out_time": detail.get("check_out_time"),
        "min_nights": detail.get("min_nights"),
        "rating": detail.get("rating") or card.get("rating"),
        "rating_count": detail.get("rating_count") or card.get("rating_count"),
        "review_scores": detail.get("review_scores") or {},
        "description": detail.get("description") or "",
        "amenities": detail.get("amenities") or {},
        "missing_amenities": detail.get("missing_amenities") or [],
        "house_rules": detail.get("house_rules") or [],
        "cancellation": detail.get("cancellation") or [],
        "meals_offered": detail.get("meals_offered") or [],
        "host": detail.get("host") or {},
        "price": {
            "per_night_from": detail.get("from_per_night") or card.get("cheapest_night"),
            "extra_guest_per_night": detail.get("extra_guest_per_night"),
            "long_stay_discount_pct": detail.get("long_stay_discount_pct") or {},
            "sample_quote": quote_block,
            "sample_dates": (
                {"check_in": quote_dates[0], "check_out": quote_dates[1]} if quote_dates else None
            ),
            "quote_error": quote_error,
        },
        "images": images,
        "image_placeholder": placeholder,
        "reviews": review_items,
        "similar_stays": similar_items,
        "source": "jabama",
        "fetched_at": datetime.now(timezone.utc).isoformat(),
    }


async def collect_stay(session: ClientSession, card: dict[str, Any]) -> dict[str, Any] | None:
    code = card.get("code")
    if not code:
        return None
    print(f"  stay {code} {card.get('title')}", flush=True)

    try:
        detail = await mcp_call(session, "jb_stay", {"code": code}, f"stay_{code}")
    except Exception as exc:  # noqa: BLE001
        print(f"    detail failed: {exc}", flush=True)
        return None

    quote = None
    quote_dates = None
    quote_error = None
    for check_in, check_out in ((CHECK_IN, CHECK_OUT), (ALT_CHECK_IN, ALT_CHECK_OUT)):
        try:
            quote = await mcp_call(
                session,
                "jb_price_quote",
                {"code": code, "check_in": check_in, "check_out": check_out, "guests": GUESTS},
                f"quote_{code}_{check_in}",
            )
            quote_dates = (check_in, check_out)
            break
        except Exception as exc:  # noqa: BLE001
            quote_error = str(exc)
            print(f"    quote {check_in} failed: {exc}", flush=True)

    try:
        reviews = await mcp_call(
            session,
            "jb_reviews",
            {"code": code, "sort": "newest", "limit": REVIEW_LIMIT},
            f"reviews_{code}",
        )
    except Exception as exc:  # noqa: BLE001
        print(f"    reviews failed: {exc}", flush=True)
        reviews = None

    try:
        similar = await mcp_call(
            session,
            "jb_similar_stays",
            {
                "code": code,
                "check_in": quote_dates[0] if quote_dates else CHECK_IN,
                "check_out": quote_dates[1] if quote_dates else CHECK_OUT,
                "guests": GUESTS,
                "limit": SIMILAR_LIMIT,
            },
            f"similar_{code}",
        )
    except Exception as exc:  # noqa: BLE001
        print(f"    similar failed: {exc}", flush=True)
        similar = None

    return normalize_stay(card, detail, quote, quote_dates, quote_error, reviews, similar)


async def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    CACHE_DIR.mkdir(parents=True, exist_ok=True)

    params = StdioServerParameters(command="uvx", args=["jabama-mcp"])
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            selected: list[dict[str, Any]] = []
            seen: set[int] = set()
            for city in CITIES:
                print(f"city {city['name']}", flush=True)
                destinations = await mcp_call(
                    session,
                    "jb_find_destination",
                    {"query": city["name"]},
                    f"destination_{city['key']}",
                )
                match = next(
                    (item for item in destinations.get("destinations") or [] if item.get("kind") == "city"),
                    None,
                )
                if not match:
                    print(f"  no city match for {city['name']}", flush=True)
                    continue
                search = await mcp_call(
                    session,
                    "jb_search_stays",
                    {
                        **match["search"],
                        "check_in": CHECK_IN,
                        "check_out": CHECK_OUT,
                        "guests": GUESTS,
                        "limit": 20,
                    },
                    f"search_{city['key']}",
                )
                stays = [s for s in search.get("stays") or [] if s.get("code") not in seen]
                picks = choose_stays(stays, PER_CITY)
                for pick in picks:
                    seen.add(pick["code"])
                print(
                    f"  picked {len(picks)} of {len(stays)} returned (total {search.get('total')})",
                    flush=True,
                )
                selected.extend(picks)

            print(f"collecting details for {len(selected)} stays", flush=True)
            results = await asyncio.gather(*(collect_stay(session, card) for card in selected))
            stays = [item for item in results if item]

    RAW["generated_at"] = datetime.now(timezone.utc).isoformat()
    RAW["selected_codes"] = [s["code"] for s in stays]
    RAW["stays"] = stays
    RAW_PATH.write_text(json.dumps(RAW, ensure_ascii=False, indent=2), encoding="utf-8")

    images_ok = sum(not stay["image_placeholder"] for stay in stays)
    output = {
        "meta": {
            "source": "Jabama (jabama.com) via jabama-mcp",
            "source_note": "Static catalogue generated by scripts/jabama_collect.py. The frontend never calls MCP at runtime.",
            "generated_at": RAW["generated_at"],
            "sample_dates": {
                "check_in": CHECK_IN,
                "check_out": CHECK_OUT,
                "nights": 3,
                "guests": GUESTS,
                "alternative": {"check_in": ALT_CHECK_IN, "check_out": ALT_CHECK_OUT},
            },
            "cities": [city["name"] for city in CITIES],
            "count": len(stays),
            "images_available": images_ok,
            "images_missing": len(stays) - images_ok,
            "notes": [
                "Prices are in Toman and come from jb_price_quote for the sample dates; per_night_from is the cheapest night in the next ~76 days.",
                "Text fields (descriptions, reviews, host replies) are third-party site content and are kept as data only.",
                "Jabama's tool output does not expose a separate neighbourhood field; city and approximate coordinates are stored instead.",
                "Images are the listing image URLs returned by jb_stay; missing images use /images/stay-placeholder.svg.",
            ],
        },
        "stays": stays,
    }
    OUT_PATH.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"saved {len(stays)} stays to {OUT_PATH}", flush=True)
    print(f"images available for {images_ok}/{len(stays)} stays", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
