#!/usr/bin/env python3
"""
Hyderabad Real Estate Report Generator
Run:  python3 generate_report.py
Output: reports/hyderabad_realestate_<timestamp>.html
"""
import asyncio
import json
import sys
import os
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "backend"))

from app.agent import run_agent
from app.scrapers.magicbricks import MagicBricksScraper
from app.scrapers.acres99 import Acres99Scraper
from app.scrapers.housing import HousingScraper
from app.scrapers.nobroker import NoBrokerScraper
from app.scrapers.squareyards import SquareYardsScraper


SCRAPERS = [MagicBricksScraper, Acres99Scraper, HousingScraper, NoBrokerScraper, SquareYardsScraper]


async def collect_data():
    print("  Running Claude agent (fetching market analysis)...")
    agent_data = await run_agent()

    print("  Running scrapers (fetching listings)...")
    all_listings = []
    scraper_status = []
    for ScraperClass in SCRAPERS:
        scraper = ScraperClass()
        result = await scraper.scrape()
        scraper_status.append({
            "source": result.source,
            "status": result.status,
            "count": len(result.listings),
        })
        for lst in result.listings:
            all_listings.append({
                "title": lst.title,
                "locality": lst.locality,
                "price_lakhs": lst.price_lakhs,
                "area_sqft": lst.area_sqft,
                "price_per_sqft": lst.price_per_sqft,
                "bedrooms": lst.bedrooms,
                "property_type": lst.property_type,
                "source": lst.source,
                "furnishing": lst.furnishing,
            })
        scraper.close()

    return agent_data, all_listings, scraper_status


def build_html(agent_data: dict, listings: list, scraper_status: list, generated_at: datetime) -> str:
    localities = agent_data.get("localities", [])
    summary = agent_data.get("market_summary", {})
    insight = agent_data.get("market_insight", "No analysis available.")

    # Sort localities by price descending
    localities_sorted = sorted(localities, key=lambda x: x.get("avg_price_per_sqft", 0), reverse=True)

    # Build chart data
    chart_labels = json.dumps([l["name"] for l in localities_sorted])
    chart_prices = json.dumps([l.get("avg_price_per_sqft", 0) for l in localities_sorted])
    chart_yoy = json.dumps([l.get("yoy_change_pct", 0) for l in localities_sorted])

    # Property type distribution
    type_counts: dict = {}
    for lst in listings:
        t = lst.get("property_type", "Other")
        type_counts[t] = type_counts.get(t, 0) + 1
    pie_labels = json.dumps(list(type_counts.keys()))
    pie_values = json.dumps(list(type_counts.values()))

    # Format insight paragraphs
    insight_html = ""
    for para in insight.split("\n\n"):
        para = para.strip()
        if not para:
            continue
        if para.startswith("**"):
            end = para.find("**", 2)
            if end != -1:
                title = para[2:end]
                body = para[end + 2:].strip()
                insight_html += f'<div class="mb-4"><h3 class="font-bold text-indigo-800 text-base mb-1">{title}</h3><p class="text-gray-700 text-sm leading-relaxed">{body}</p></div>'
                continue
        insight_html += f'<p class="text-gray-700 text-sm leading-relaxed mb-4">{para}</p>'

    # Listings rows
    listing_rows = ""
    for lst in sorted(listings, key=lambda x: x.get("price_lakhs", 0), reverse=True)[:30]:
        price = lst.get("price_lakhs", 0)
        price_str = f"₹{price/100:.2f} Cr" if price >= 100 else f"₹{price:.1f}L"
        beds = f"{lst['bedrooms']} BHK" if lst.get("bedrooms") else "-"
        source_colors = {
            "MagicBricks": "#f97316", "99acres": "#3b82f6",
            "Housing.com": "#10b981", "NoBroker": "#8b5cf6", "Square Yards": "#ec4899",
        }
        color = source_colors.get(lst.get("source", ""), "#6b7280")
        listing_rows += f"""
        <tr class="border-b border-gray-50 hover:bg-gray-50">
          <td class="py-2.5 px-3 text-sm text-gray-800">{lst.get('title','')[:45]}</td>
          <td class="py-2.5 px-3 text-sm text-gray-600">{lst.get('locality','')}</td>
          <td class="py-2.5 px-3 text-sm font-semibold text-gray-900 text-right">{price_str}</td>
          <td class="py-2.5 px-3 text-sm text-gray-600 text-right">{lst.get('area_sqft',0):,.0f} sqft</td>
          <td class="py-2.5 px-3 text-sm font-medium text-indigo-600 text-right">₹{lst.get('price_per_sqft',0):,.0f}</td>
          <td class="py-2.5 px-3 text-sm text-gray-600 text-center">{beds}</td>
          <td class="py-2.5 px-3 text-sm text-gray-600 text-center">{lst.get('property_type','')}</td>
          <td class="py-2.5 px-3 text-center">
            <span class="px-2 py-0.5 rounded-full text-xs font-medium text-white" style="background:{color}">{lst.get('source','')}</span>
          </td>
        </tr>"""

    # Locality table rows
    locality_rows = ""
    demand_colors = {"High": "bg-green-100 text-green-800", "Medium": "bg-yellow-100 text-yellow-800", "Low": "bg-gray-100 text-gray-600"}
    for loc in localities_sorted:
        yoy = loc.get("yoy_change_pct", 0)
        yoy_color = "text-green-600" if yoy > 0 else "text-red-500"
        demand = loc.get("demand_level", "Medium")
        dc = demand_colors.get(demand, "bg-gray-100 text-gray-600")
        bhk2 = f"₹{loc['avg_price_2bhk_lakhs']:.0f}L" if loc.get("avg_price_2bhk_lakhs") else "-"
        bhk3 = f"₹{loc['avg_price_3bhk_lakhs']:.0f}L" if loc.get("avg_price_3bhk_lakhs") else "-"
        locality_rows += f"""
        <tr class="border-b border-gray-50 hover:bg-indigo-50/30">
          <td class="py-3 px-4 font-semibold text-gray-900">{loc['name']}</td>
          <td class="py-3 px-4 text-right font-bold text-indigo-700">₹{loc.get('avg_price_per_sqft',0):,.0f}</td>
          <td class="py-3 px-4 text-right text-sm text-gray-500">₹{loc.get('min_price_per_sqft',0) or 0:,.0f} – ₹{loc.get('max_price_per_sqft',0) or 0:,.0f}</td>
          <td class="py-3 px-4 text-right text-sm {yoy_color} font-semibold">{yoy:+.1f}%</td>
          <td class="py-3 px-4 text-center text-sm">{bhk2}</td>
          <td class="py-3 px-4 text-center text-sm">{bhk3}</td>
          <td class="py-3 px-4 text-center">
            <span class="px-2 py-0.5 rounded-full text-xs font-medium {dc}">{demand}</span>
          </td>
          <td class="py-3 px-4 text-right text-sm text-gray-500">{loc.get('listing_count',0)}</td>
        </tr>"""

    # Scraper status badges
    source_status_html = ""
    for s in scraper_status:
        ok = s["status"] == "success"
        color = "bg-green-100 text-green-800 border-green-200" if ok else "bg-amber-100 text-amber-800 border-amber-200"
        icon = "✓" if ok else "↻"
        source_status_html += f'<div class="flex items-center gap-2 px-3 py-2 rounded-lg border {color} text-sm"><span class="font-bold">{icon}</span><span class="font-medium">{s["source"]}</span><span class="opacity-70">({s["count"]} listings)</span></div>'

    ts_display = generated_at.strftime("%d %B %Y, %I:%M %p")
    ts_file = generated_at.strftime("%Y-%m-%d %H:%M")

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>Hyderabad Real Estate Report — {ts_display}</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
  <style>
    body {{ font-family: system-ui, -apple-system, sans-serif; }}
    @media print {{ .no-print {{ display: none; }} }}
  </style>
</head>
<body class="bg-gray-50 min-h-screen">

  <!-- Header -->
  <div class="bg-gradient-to-r from-indigo-900 via-indigo-800 to-purple-900 text-white">
    <div class="max-w-6xl mx-auto px-4 py-8">
      <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 class="text-2xl font-bold tracking-tight">🏘️ Hyderabad Real Estate Intelligence</h1>
          <p class="text-indigo-300 text-sm mt-1">AI-powered market analysis · Powered by Claude Code</p>
        </div>
        <div class="text-right">
          <p class="text-indigo-300 text-xs uppercase tracking-wide">Generated</p>
          <p class="text-white text-lg font-semibold">{ts_display}</p>
        </div>
      </div>
    </div>
  </div>

  <div class="max-w-6xl mx-auto px-4 py-8 space-y-8">

    <!-- KPI Cards -->
    <div class="grid grid-cols-2 lg:grid-cols-4 gap-4">
      <div class="bg-white rounded-2xl shadow-sm border border-gray-100 p-5">
        <p class="text-xs text-gray-500 uppercase tracking-wide">City Avg</p>
        <p class="text-2xl font-bold text-indigo-700 mt-1">₹{summary.get('avg_price_per_sqft',0):,.0f}</p>
        <p class="text-xs text-gray-400 mt-1">per sq ft</p>
      </div>
      <div class="bg-white rounded-2xl shadow-sm border border-gray-100 p-5">
        <p class="text-xs text-gray-500 uppercase tracking-wide">YoY Growth</p>
        <p class="text-2xl font-bold text-green-600 mt-1">+{summary.get('yoy_change_pct',0):.1f}%</p>
        <p class="text-xs text-gray-400 mt-1">year on year</p>
      </div>
      <div class="bg-white rounded-2xl shadow-sm border border-gray-100 p-5">
        <p class="text-xs text-gray-500 uppercase tracking-wide">Hottest Area</p>
        <p class="text-xl font-bold text-rose-600 mt-1 leading-tight">{summary.get('hottest_locality','—')}</p>
        <p class="text-xs text-gray-400 mt-1">highest growth</p>
      </div>
      <div class="bg-white rounded-2xl shadow-sm border border-gray-100 p-5">
        <p class="text-xs text-gray-500 uppercase tracking-wide">Localities</p>
        <p class="text-2xl font-bold text-amber-600 mt-1">{len(localities_sorted)}</p>
        <p class="text-xs text-gray-400 mt-1">micro-markets tracked</p>
      </div>
    </div>

    <!-- AI Insights -->
    <div class="bg-gradient-to-br from-indigo-50 to-purple-50 rounded-2xl border border-indigo-100 p-6">
      <div class="flex items-center gap-3 mb-5">
        <div class="bg-indigo-600 rounded-xl p-2">
          <span class="text-white text-lg">✦</span>
        </div>
        <div>
          <h2 class="text-lg font-bold text-gray-900">AI Market Analysis</h2>
          <p class="text-xs text-gray-500">Claude Code analysis · {ts_display}</p>
        </div>
      </div>
      <div>{insight_html}</div>
    </div>

    <!-- Charts row -->
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <div class="lg:col-span-2 bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
        <h2 class="text-base font-bold text-gray-900 mb-4">Price by Locality (₹/sqft)</h2>
        <canvas id="barChart" height="200"></canvas>
      </div>
      <div class="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
        <h2 class="text-base font-bold text-gray-900 mb-4">Property Types</h2>
        <canvas id="pieChart" height="200"></canvas>
      </div>
    </div>

    <!-- Locality Price Table -->
    <div class="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
      <div class="px-6 py-4 border-b border-gray-100">
        <h2 class="text-base font-bold text-gray-900">Locality-wise Prices</h2>
        <p class="text-xs text-gray-500 mt-0.5">Sorted by avg price/sqft · June 2026</p>
      </div>
      <div class="overflow-x-auto">
        <table class="min-w-full text-sm">
          <thead class="bg-gray-50">
            <tr>
              <th class="py-3 px-4 text-left text-xs font-semibold text-gray-500 uppercase">Locality</th>
              <th class="py-3 px-4 text-right text-xs font-semibold text-gray-500 uppercase">Avg ₹/sqft</th>
              <th class="py-3 px-4 text-right text-xs font-semibold text-gray-500 uppercase">Range</th>
              <th class="py-3 px-4 text-right text-xs font-semibold text-gray-500 uppercase">YoY</th>
              <th class="py-3 px-4 text-center text-xs font-semibold text-gray-500 uppercase">2BHK Avg</th>
              <th class="py-3 px-4 text-center text-xs font-semibold text-gray-500 uppercase">3BHK Avg</th>
              <th class="py-3 px-4 text-center text-xs font-semibold text-gray-500 uppercase">Demand</th>
              <th class="py-3 px-4 text-right text-xs font-semibold text-gray-500 uppercase">Listings</th>
            </tr>
          </thead>
          <tbody>{locality_rows}</tbody>
        </table>
      </div>
    </div>

    <!-- Recent Listings -->
    <div class="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
      <div class="px-6 py-4 border-b border-gray-100">
        <h2 class="text-base font-bold text-gray-900">Recent Property Listings</h2>
        <p class="text-xs text-gray-500 mt-0.5">Top {min(30, len(listings))} listings by price · All sources</p>
      </div>
      <div class="overflow-x-auto">
        <table class="min-w-full text-sm">
          <thead class="bg-gray-50">
            <tr>
              <th class="py-3 px-3 text-left text-xs font-semibold text-gray-500 uppercase">Property</th>
              <th class="py-3 px-3 text-left text-xs font-semibold text-gray-500 uppercase">Locality</th>
              <th class="py-3 px-3 text-right text-xs font-semibold text-gray-500 uppercase">Price</th>
              <th class="py-3 px-3 text-right text-xs font-semibold text-gray-500 uppercase">Area</th>
              <th class="py-3 px-3 text-right text-xs font-semibold text-gray-500 uppercase">₹/sqft</th>
              <th class="py-3 px-3 text-center text-xs font-semibold text-gray-500 uppercase">BHK</th>
              <th class="py-3 px-3 text-center text-xs font-semibold text-gray-500 uppercase">Type</th>
              <th class="py-3 px-3 text-center text-xs font-semibold text-gray-500 uppercase">Source</th>
            </tr>
          </thead>
          <tbody>{listing_rows}</tbody>
        </table>
      </div>
    </div>

    <!-- Data Sources -->
    <div class="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
      <h2 class="text-base font-bold text-gray-900 mb-4">Data Sources</h2>
      <div class="flex flex-wrap gap-3">{source_status_html}</div>
    </div>

    <!-- Footer -->
    <div class="text-center text-xs text-gray-400 pb-6">
      Generated by Hyderabad Real Estate Intelligence Agent · Claude Code · {ts_display}
    </div>

  </div>

  <script>
    // Bar chart — price by locality
    new Chart(document.getElementById('barChart'), {{
      type: 'bar',
      data: {{
        labels: {chart_labels},
        datasets: [{{
          label: 'Avg ₹/sqft',
          data: {chart_prices},
          backgroundColor: 'rgba(99,102,241,0.75)',
          borderRadius: 6,
        }}, {{
          label: 'YoY %',
          data: {chart_yoy},
          backgroundColor: 'rgba(16,185,129,0.6)',
          borderRadius: 6,
          yAxisID: 'y2',
        }}]
      }},
      options: {{
        responsive: true,
        plugins: {{ legend: {{ position: 'top' }} }},
        scales: {{
          y: {{ ticks: {{ callback: v => '₹' + v.toLocaleString('en-IN') }} }},
          y2: {{ position: 'right', ticks: {{ callback: v => v + '%' }}, grid: {{ drawOnChartArea: false }} }},
          x: {{ ticks: {{ maxRotation: 45, font: {{ size: 10 }} }} }}
        }}
      }}
    }});

    // Pie chart — property types
    new Chart(document.getElementById('pieChart'), {{
      type: 'doughnut',
      data: {{
        labels: {pie_labels},
        datasets: [{{
          data: {pie_values},
          backgroundColor: ['#6366f1','#10b981','#f59e0b','#ef4444','#8b5cf6'],
        }}]
      }},
      options: {{
        responsive: true,
        plugins: {{ legend: {{ position: 'bottom', labels: {{ font: {{ size: 11 }} }} }} }}
      }}
    }});
  </script>

</body>
</html>"""


async def main():
    generated_at = datetime.now()
    ts = generated_at.strftime("%Y-%m-%d_%H-%M")

    print(f"\n{'='*55}")
    print(f"  Hyderabad Real Estate Report Generator")
    print(f"  {generated_at.strftime('%d %B %Y, %I:%M %p')}")
    print(f"{'='*55}\n")

    agent_data, listings, scraper_status = await collect_data()

    print(f"  Building HTML report...")
    html = build_html(agent_data, listings, scraper_status, generated_at)

    out_dir = Path(__file__).parent / "reports"
    out_dir.mkdir(exist_ok=True)
    out_file = out_dir / f"hyderabad_realestate_{ts}.html"
    out_file.write_text(html, encoding="utf-8")

    # Also write a stable "latest" copy for easy access
    latest = out_dir / "latest.html"
    latest.write_text(html, encoding="utf-8")

    size_kb = out_file.stat().st_size / 1024
    locs = agent_data.get("localities", [])
    summary = agent_data.get("market_summary", {})

    print(f"\n{'='*55}")
    print(f"  Report saved!")
    print(f"  {out_file}")
    print(f"  Size : {size_kb:.1f} KB")
    print(f"  Localities : {len(locs)}")
    print(f"  Listings   : {len(listings)}")
    print(f"  City avg   : Rs{summary.get('avg_price_per_sqft',0):,.0f}/sqft")
    print(f"  YoY growth : +{summary.get('yoy_change_pct',0):.1f}%")
    print(f"  Hottest    : {summary.get('hottest_locality','')}")
    print(f"\n  Open in browser:")
    print(f"  file://{out_file.resolve()}")
    print(f"{'='*55}\n")

    return str(out_file)


if __name__ == "__main__":
    asyncio.run(main())
