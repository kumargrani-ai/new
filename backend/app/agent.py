"""
Hyderabad Real Estate Intelligence Agent.
Uses the `claude` CLI (Claude Code) via subprocess — no API key required.
"""
import asyncio
import json
import logging
import re
import subprocess
from typing import Any, Dict

logger = logging.getLogger(__name__)

LOCALITIES = [
    "Gachibowli", "Hitech City", "Kondapur", "Banjara Hills", "Jubilee Hills",
    "Kukatpally", "Miyapur", "Manikonda", "Nallagandla", "Kokapet",
    "Kompally", "Bachupally", "Madhapur", "Uppal", "LB Nagar",
    "Shamshabad", "Attapur",
]

PRICE_PROMPT = """You are a Hyderabad real estate data analyst.
Return ONLY a raw JSON array (no markdown fences, no explanation) for these localities: """ + ", ".join(LOCALITIES) + """.

Each element must be exactly:
{"name":"<locality>","avg_price_per_sqft":<number>,"min_price_per_sqft":<number>,"max_price_per_sqft":<number>,"avg_price_2bhk_lakhs":<number>,"avg_price_3bhk_lakhs":<number>,"yoy_change_pct":<number>,"demand_level":"High"|"Medium"|"Low","listing_count":<integer>}

Use realistic June 2026 Hyderabad prices (INR):
Jubilee Hills/Banjara Hills: 12000-16000/sqft | Hitech City/Madhapur: 8500-11000 | Gachibowli/Kokapet: 7500-10000
Kondapur/Nallagandla: 6500-8500 | Kukatpally/Miyapur: 5500-7500 | Manikonda/Bachupally/Kompally: 4500-6500
LB Nagar/Uppal/Attapur: 4000-5500 | Shamshabad: 3000-4500

Return ONLY the JSON array."""

INSIGHT_PROMPT = """You are a senior Hyderabad real estate market analyst. Write a market analysis for June 2026.

Return ONLY a raw JSON object (no markdown fences):
{"market_insight":"<5-6 paragraphs>","market_summary":{"avg_price_per_sqft":<number>,"total_listings":<integer>,"hottest_locality":"<name>","yoy_change_pct":<number>}}

Rules for market_insight:
- Start each paragraph with **Bold Heading**:
- Cover: overall market, western IT corridor, premium Banjara/Jubilee, mid-segment, emerging areas, investment recommendations
- Be specific with numbers and locality names

Return ONLY the JSON object."""


def _run_claude(prompt: str, timeout: int = 120) -> str:
    """Synchronous wrapper around claude CLI call."""
    result = subprocess.run(
        ["claude", "-p", prompt],
        capture_output=True,
        text=True,
        timeout=timeout,
        stdin=subprocess.DEVNULL,
    )
    if result.returncode != 0:
        logger.warning(f"claude CLI rc={result.returncode}: {result.stderr[:200]}")
    return result.stdout.strip()


def _extract_json(text: str) -> Any:
    """Extract the first valid JSON value from CLI output."""
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    # Strip markdown fences
    clean = re.sub(r"```(?:json)?", "", text).strip()
    try:
        return json.loads(clean)
    except json.JSONDecodeError:
        pass
    # Find outermost [ ... ] or { ... }
    for opener, closer in [("[", "]"), ("{", "}")]:
        start = text.find(opener)
        end = text.rfind(closer)
        if start != -1 and end > start:
            try:
                return json.loads(text[start: end + 1])
            except json.JSONDecodeError:
                continue
    logger.warning(f"JSON parse failed. Output snippet: {text[:300]}")
    return None


NEW_LAUNCHES_PROMPT = """You are a Hyderabad real estate market analyst writing a market intelligence brief.
Based on your knowledge of Hyderabad's real estate market, describe new residential projects
launched or under construction by major builders as of mid-2026.

NOTE: This is illustrative market intelligence data — do NOT include RERA numbers or phone numbers.

Return ONLY a raw JSON array (no markdown, no explanation):
[{
  "builder": "MyHome Group",
  "project_name": "MyHome Tridasa",
  "locality": "Kokapet",
  "configuration": "3BHK, 4BHK",
  "size_range": "2100 - 3800 sqft",
  "price_range": "Rs 1.8 Cr - Rs 3.5 Cr",
  "price_per_sqft": 9200,
  "launch_date": "Q1 2026",
  "possession_date": "Dec 2028",
  "status": "New Launch",
  "highlights": "IGBC Gold certified, sky deck, 500m from Financial District metro"
}]

Include 15+ representative projects from:
MyHome Group, Aparna Constructions, Ramky Group, Prestige Group, Sobha Limited,
Brigade Group, Godrej Properties, Purva Group, Mahindra Lifespaces, Lodha Group,
Phoenix Group, Incor, Vertex Homes, Aliens Group

Focus areas: Kokapet, Nallagandla, Bachupally, Financial District, Gachibowli,
Kondapur, Kompally, Shamshabad corridor, Tellapur, Mokila

Status options: "New Launch", "Under Construction", "Ready to Move", "Pre-Launch"

Return ONLY the JSON array."""


async def run_agent() -> Dict[str, Any]:
    """
    Run three Claude CLI calls in parallel:
      1. Locality price data (JSON array)
      2. Market insight + summary (JSON object)
      3. New launches from corporate builders (JSON array)
    """
    logger.info("Starting Claude Code agent...")
    loop = asyncio.get_event_loop()

    price_future   = loop.run_in_executor(None, _run_claude, PRICE_PROMPT, 120)
    insight_future = loop.run_in_executor(None, _run_claude, INSIGHT_PROMPT, 120)
    launches_future = loop.run_in_executor(None, _run_claude, NEW_LAUNCHES_PROMPT, 120)

    price_output, insight_output, launches_output = await asyncio.gather(
        price_future, insight_future, launches_future
    )

    localities    = _extract_json(price_output)
    insight_data  = _extract_json(insight_output)
    new_launches  = _extract_json(launches_output)

    if not isinstance(localities, list):
        logger.error("Localities response was not a list")
        localities = []

    if not isinstance(insight_data, dict):
        logger.error("Insight response was not a dict")
        insight_data = {}

    if not isinstance(new_launches, list):
        logger.warning("New launches response was not a list, using empty")
        new_launches = []

    logger.info(
        f"Agent: {len(localities)} localities, "
        f"insight={'yes' if insight_data else 'no'}, "
        f"{len(new_launches)} new launches"
    )

    return {
        "localities": localities,
        "market_insight": insight_data.get("market_insight", ""),
        "market_summary": insight_data.get("market_summary", {
            "avg_price_per_sqft": 0,
            "total_listings": 0,
            "hottest_locality": "",
            "yoy_change_pct": 0,
        }),
        "new_launches": new_launches,
    }
