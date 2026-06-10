"""
Hyderabad Real Estate Intelligence Agent powered by Claude.
Uses tool-use to gather, analyze and summarize market data.
"""
import json
import logging
from datetime import datetime
from typing import Any, Dict, List

import anthropic
import httpx

logger = logging.getLogger(__name__)

AGENT_SYSTEM_PROMPT = """You are a senior real estate market analyst specializing in Hyderabad, India.
Your job is to gather current real estate market data and provide actionable insights for investors and buyers.

Focus areas:
- Residential: apartments, villas, independent houses, plots
- Key micro-markets: Gachibowli, Hitech City, Kondapur, Banjara Hills, Jubilee Hills,
  Kukatpally, Miyapur, Manikonda, Nallagandla, Kokapet, Kompally, Bachupally
- Price trends (YoY changes), hottest localities, emerging areas
- Affordable vs premium segments

When saving market data, extract realistic price-per-sqft values based on what you know about
Hyderabad real estate as of 2026. Provide concrete insights that help buyers make decisions.
"""

TOOLS = [
    {
        "name": "search_web",
        "description": (
            "Search the web for latest Hyderabad real estate prices, market trends, "
            "and property news. Use this to gather current data."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query for real estate information",
                }
            },
            "required": ["query"],
        },
    },
    {
        "name": "save_market_data",
        "description": (
            "Save the extracted Hyderabad real estate market data to the database. "
            "Call this after gathering sufficient information."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "localities": {
                    "type": "array",
                    "description": "Price data per Hyderabad locality",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string", "description": "Locality name"},
                            "avg_price_per_sqft": {
                                "type": "number",
                                "description": "Average price per sq ft in INR",
                            },
                            "min_price_per_sqft": {"type": "number"},
                            "max_price_per_sqft": {"type": "number"},
                            "avg_price_2bhk_lakhs": {
                                "type": "number",
                                "description": "Avg 2BHK price in lakhs",
                            },
                            "avg_price_3bhk_lakhs": {
                                "type": "number",
                                "description": "Avg 3BHK price in lakhs",
                            },
                            "yoy_change_pct": {
                                "type": "number",
                                "description": "Year-over-year price change %",
                            },
                            "demand_level": {
                                "type": "string",
                                "enum": ["High", "Medium", "Low"],
                            },
                            "listing_count": {"type": "integer"},
                        },
                        "required": ["name", "avg_price_per_sqft"],
                    },
                },
                "market_insight": {
                    "type": "string",
                    "description": (
                        "Comprehensive AI analysis of the Hyderabad real estate market "
                        "covering trends, hotspots, investment opportunities, and risks. "
                        "Write 4-6 paragraphs."
                    ),
                },
                "market_summary": {
                    "type": "object",
                    "description": "Key market metrics",
                    "properties": {
                        "avg_price_per_sqft": {"type": "number"},
                        "total_listings": {"type": "integer"},
                        "hottest_locality": {"type": "string"},
                        "yoy_change_pct": {"type": "number"},
                    },
                    "required": ["avg_price_per_sqft", "hottest_locality"],
                },
            },
            "required": ["localities", "market_insight", "market_summary"],
        },
    },
]


class RealEstateAgent:
    def __init__(self, anthropic_api_key: str | None = None):
        self.client = anthropic.Anthropic(api_key=anthropic_api_key) if anthropic_api_key else anthropic.Anthropic()
        self.model = "claude-sonnet-4-6"
        self._saved_data: Dict[str, Any] = {}

    async def run(self) -> Dict[str, Any]:
        """Run the agent to gather and analyze Hyderabad real estate data."""
        messages = [
            {
                "role": "user",
                "content": (
                    "Please gather current Hyderabad real estate market data for June 2026. "
                    "Search for price trends, locality-wise rates, and market conditions. "
                    "Cover at least 12 major localities including Gachibowli, Hitech City, "
                    "Kondapur, Banjara Hills, Jubilee Hills, Kukatpally, Miyapur, Manikonda, "
                    "Nallagandla, Kokapet, Kompally, and Bachupally. "
                    "Then save the data with your analysis."
                ),
            }
        ]

        max_iterations = 8
        for iteration in range(max_iterations):
            logger.info(f"Agent iteration {iteration + 1}")
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                system=AGENT_SYSTEM_PROMPT,
                tools=TOOLS,
                messages=messages,
            )

            # Add assistant response to history
            messages.append({"role": "assistant", "content": response.content})

            if response.stop_reason == "end_turn":
                logger.info("Agent completed (end_turn)")
                break

            if response.stop_reason == "tool_use":
                tool_results = []
                for block in response.content:
                    if block.type == "tool_use":
                        result = await self._execute_tool(block.name, block.input)
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": json.dumps(result),
                        })

                messages.append({"role": "user", "content": tool_results})

                # If save_market_data was called, we have what we need
                if "save_market_data" in [b.name for b in response.content if hasattr(b, "name")]:
                    logger.info("Market data saved, agent done")
                    break

        return self._saved_data

    async def _execute_tool(self, name: str, inputs: Dict[str, Any]) -> Any:
        if name == "search_web":
            return await self._web_search(inputs["query"])
        if name == "save_market_data":
            self._saved_data = inputs
            return {"status": "saved", "localities_count": len(inputs.get("localities", []))}
        return {"error": f"Unknown tool: {name}"}

    async def _web_search(self, query: str) -> Dict[str, Any]:
        """Search using DuckDuckGo's text search (no API key required)."""
        search_url = "https://html.duckduckgo.com/html/"
        try:
            async with httpx.AsyncClient(
                headers={
                    "User-Agent": (
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"
                    )
                },
                timeout=15.0,
                follow_redirects=True,
            ) as client:
                resp = await client.post(search_url, data={"q": query, "kl": "in-en"})

            from bs4 import BeautifulSoup
            soup = BeautifulSoup(resp.text, "lxml")
            results = []
            for result in soup.select(".result")[:5]:
                title_el = result.select_one(".result__title")
                snippet_el = result.select_one(".result__snippet")
                url_el = result.select_one(".result__url")
                if title_el and snippet_el:
                    results.append({
                        "title": title_el.get_text(strip=True),
                        "snippet": snippet_el.get_text(strip=True),
                        "url": url_el.get_text(strip=True) if url_el else "",
                    })

            return {"query": query, "results": results, "count": len(results)}

        except Exception as e:
            logger.warning(f"Web search failed: {e}")
            return {
                "query": query,
                "results": [],
                "note": "Search unavailable; use your training data for Hyderabad market context.",
            }
