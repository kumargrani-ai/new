#!/usr/bin/env python3
"""
Hyderabad Real Estate Report Generator
Usage:
  python3 generate_report.py                          # generate HTML only
  python3 generate_report.py --email me@example.com  # generate + email
"""
import argparse
import asyncio
import json
import os
import re
import smtplib
import sys
from datetime import datetime
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "backend"))

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent / "backend" / ".env")

from app.agent import run_agent
from app.scrapers.magicbricks import MagicBricksScraper
from app.scrapers.acres99 import Acres99Scraper
from app.scrapers.housing import HousingScraper
from app.scrapers.nobroker import NoBrokerScraper
from app.scrapers.squareyards import SquareYardsScraper

SCRAPERS = [MagicBricksScraper, Acres99Scraper, HousingScraper, NoBrokerScraper, SquareYardsScraper]

STATUS_COLORS = {
    "New Launch":        ("bg-green-100",  "text-green-800",  "border-green-300"),
    "Under Construction":("bg-yellow-100", "text-yellow-800", "border-yellow-300"),
    "Ready to Move":     ("bg-blue-100",   "text-blue-800",   "border-blue-300"),
    "Pre-Launch":        ("bg-purple-100", "text-purple-800", "border-purple-300"),
}
BUILDER_LOGOS = {
    "MyHome Group":         "🏗️", "My Home Constructions": "🏗️",
    "Aparna Constructions": "🏢", "Ramky Group":           "🏛️",
    "Prestige Group":       "⭐", "Sobha Limited":         "💎",
    "Brigade Group":        "🏙️", "Godrej Properties":    "🌿",
    "Purva Group":          "🏠", "Mahindra Lifespaces":   "🔷",
    "Lodha Group":          "🏰", "Phoenix Group":         "🔥",
    "Incor":                "🌆", "Vertex Homes":          "📐",
    "Aliens Group":         "🚀",
}


# ── Data collection ──────────────────────────────────────────────────────────

async def collect_data():
    print("  [1/2] Running Claude agent (prices + insights + new launches)...")
    agent_data = await run_agent()

    print("  [2/2] Running scrapers (property listings)...")
    all_listings, scraper_status = [], []
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
                "title":          lst.title,
                "locality":       lst.locality,
                "price_lakhs":    lst.price_lakhs,
                "area_sqft":      lst.area_sqft,
                "price_per_sqft": lst.price_per_sqft,
                "bedrooms":       lst.bedrooms,
                "property_type":  lst.property_type,
                "source":         lst.source,
                "furnishing":     lst.furnishing,
                "posted_date":    lst.posted_date,
                "contact_number": lst.contact_number,
            })
        scraper.close()

    return agent_data, all_listings, scraper_status


# ── HTML builder ─────────────────────────────────────────────────────────────

def build_html(agent_data: dict, listings: list, scraper_status: list, ts: datetime) -> str:
    localities    = sorted(agent_data.get("localities", []),
                           key=lambda x: x.get("avg_price_per_sqft", 0), reverse=True)
    summary       = agent_data.get("market_summary", {})
    insight       = agent_data.get("market_insight", "No analysis available.")
    new_launches  = agent_data.get("new_launches", [])
    ts_display    = ts.strftime("%d %B %Y, %I:%M %p")

    # ── Charts ────────────────────────────────────────────────────────────────
    chart_labels  = json.dumps([l["name"] for l in localities])
    chart_prices  = json.dumps([l.get("avg_price_per_sqft", 0) for l in localities])
    chart_yoy     = json.dumps([l.get("yoy_change_pct", 0) for l in localities])

    type_counts: dict = {}
    for lst in listings:
        t = lst.get("property_type", "Other")
        type_counts[t] = type_counts.get(t, 0) + 1
    pie_labels = json.dumps(list(type_counts.keys()))
    pie_values = json.dumps(list(type_counts.values()))

    # ── AI insight paragraphs ─────────────────────────────────────────────────
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
                insight_html += (
                    f'<div class="mb-4">'
                    f'<h3 class="font-bold text-indigo-800 text-sm mb-1">{title}</h3>'
                    f'<p class="text-gray-700 text-sm leading-relaxed">{body}</p>'
                    f'</div>'
                )
                continue
        insight_html += f'<p class="text-gray-700 text-sm leading-relaxed mb-3">{para}</p>'

    # ── New launches cards ────────────────────────────────────────────────────
    launch_cards = ""
    for proj in new_launches:
        status   = proj.get("status", "New Launch")
        bg, tc, bc = STATUS_COLORS.get(status, ("bg-gray-100", "text-gray-800", "border-gray-300"))
        icon     = BUILDER_LOGOS.get(proj.get("builder", ""), "🏢")
        launch_cards += f"""
        <div class="bg-white rounded-2xl border {bc} shadow-sm overflow-hidden flex flex-col">
          <div class="px-4 pt-4 pb-3 flex items-start gap-3">
            <span class="text-3xl">{icon}</span>
            <div class="flex-1 min-w-0">
              <p class="text-xs text-gray-400 font-medium uppercase tracking-wide">{proj.get('builder','')}</p>
              <h3 class="font-bold text-gray-900 text-base leading-tight">{proj.get('project_name','')}</h3>
              <p class="text-sm text-indigo-600 font-medium mt-0.5">📍 {proj.get('locality','')}</p>
            </div>
            <span class="shrink-0 px-2 py-1 rounded-full text-xs font-bold {bg} {tc} border {bc}">{status}</span>
          </div>
          <div class="px-4 pb-3 grid grid-cols-2 gap-x-4 gap-y-1.5 text-sm border-t border-gray-50 pt-3">
            <div><span class="text-gray-400">Config</span><br><span class="font-semibold text-gray-800">{proj.get('configuration','—')}</span></div>
            <div><span class="text-gray-400">Size</span><br><span class="font-semibold text-gray-800">{proj.get('size_range','—')}</span></div>
            <div><span class="text-gray-400">Price</span><br><span class="font-bold text-green-700">{proj.get('price_range','—')}</span></div>
            <div><span class="text-gray-400">Rate</span><br><span class="font-semibold text-indigo-700">Rs {proj.get('price_per_sqft',0):,}/sqft</span></div>
            <div><span class="text-gray-400">Launch</span><br><span class="font-semibold text-gray-700">{proj.get('launch_date','—')}</span></div>
            <div><span class="text-gray-400">Possession</span><br><span class="font-semibold text-gray-700">{proj.get('possession_date','—')}</span></div>
          </div>
          <div class="px-4 pb-4 text-xs text-gray-500 italic leading-snug">
            {proj.get('highlights','')[:120]}
          </div>
        </div>"""

    if not launch_cards:
        launch_cards = '<p class="text-gray-400 col-span-full text-sm text-center py-8">No new launch data available. Run again to fetch.</p>'

    # ── Locality table rows ───────────────────────────────────────────────────
    demand_cls = {
        "High":   "bg-green-100 text-green-800",
        "Medium": "bg-yellow-100 text-yellow-800",
        "Low":    "bg-gray-100 text-gray-500",
    }
    locality_rows = ""
    for loc in localities:
        yoy   = loc.get("yoy_change_pct", 0)
        yc    = "text-green-600 font-semibold" if yoy > 0 else "text-red-500 font-semibold"
        dc    = demand_cls.get(loc.get("demand_level", "Medium"), "bg-gray-100 text-gray-500")
        bhk2  = f"Rs{loc['avg_price_2bhk_lakhs']:.0f}L" if loc.get("avg_price_2bhk_lakhs") else "—"
        bhk3  = f"Rs{loc['avg_price_3bhk_lakhs']:.0f}L" if loc.get("avg_price_3bhk_lakhs") else "—"
        lo    = f"Rs{loc['min_price_per_sqft']:,.0f}" if loc.get("min_price_per_sqft") else "—"
        hi    = f"Rs{loc['max_price_per_sqft']:,.0f}" if loc.get("max_price_per_sqft") else "—"
        locality_rows += f"""
        <tr class="border-b border-gray-50 hover:bg-indigo-50/30 transition-colors">
          <td class="py-3 px-4 font-semibold text-gray-900 text-sm">{loc['name']}</td>
          <td class="py-3 px-4 text-right font-bold text-indigo-700">Rs {loc.get('avg_price_per_sqft',0):,.0f}</td>
          <td class="py-3 px-4 text-right text-xs text-gray-500">{lo} – {hi}</td>
          <td class="py-3 px-4 text-right text-sm {yc}">{yoy:+.1f}%</td>
          <td class="py-3 px-4 text-center text-sm text-gray-700">{bhk2}</td>
          <td class="py-3 px-4 text-center text-sm text-gray-700">{bhk3}</td>
          <td class="py-3 px-4 text-center"><span class="px-2 py-0.5 rounded-full text-xs font-medium {dc}">{loc.get('demand_level','?')}</span></td>
          <td class="py-3 px-4 text-right text-sm text-gray-500">{loc.get('listing_count',0)}</td>
        </tr>"""

    # ── Listings table rows ───────────────────────────────────────────────────
    src_colors = {
        "MagicBricks":  "#f97316",
        "99acres":      "#3b82f6",
        "Housing.com":  "#10b981",
        "NoBroker":     "#8b5cf6",
        "Square Yards": "#ec4899",
    }
    listing_rows = ""
    for lst in sorted(listings, key=lambda x: x.get("price_lakhs", 0), reverse=True)[:40]:
        price = lst.get("price_lakhs", 0)
        price_str = f"Rs {price/100:.2f} Cr" if price >= 100 else f"Rs {price:.1f}L"
        beds  = f"{lst['bedrooms']} BHK" if lst.get("bedrooms") else "—"
        clr   = src_colors.get(lst.get("source", ""), "#6b7280")
        posted = lst.get("posted_date") or "—"
        contact = lst.get("contact_number") or "—"
        contact_cell = (
            f'<a href="tel:{re.sub(r"[^0-9+]", "", contact)}" '
            f'class="text-indigo-600 hover:underline whitespace-nowrap">{contact}</a>'
            if contact != "—" else '<span class="text-gray-300">—</span>'
        )
        listing_rows += f"""
        <tr class="border-b border-gray-50 hover:bg-gray-50 transition-colors">
          <td class="py-2.5 px-3 text-xs text-gray-400 whitespace-nowrap">{posted}</td>
          <td class="py-2.5 px-3 text-sm text-gray-800 max-w-xs truncate">{lst.get('title','')[:50]}</td>
          <td class="py-2.5 px-3 text-sm text-gray-600 whitespace-nowrap">{lst.get('locality','')}</td>
          <td class="py-2.5 px-3 text-sm font-bold text-gray-900 text-right whitespace-nowrap">{price_str}</td>
          <td class="py-2.5 px-3 text-sm text-gray-600 text-right whitespace-nowrap">{lst.get('area_sqft',0):,.0f} sqft</td>
          <td class="py-2.5 px-3 text-sm font-medium text-indigo-600 text-right whitespace-nowrap">Rs {lst.get('price_per_sqft',0):,.0f}</td>
          <td class="py-2.5 px-3 text-sm text-gray-600 text-center">{beds}</td>
          <td class="py-2.5 px-3 text-sm text-gray-600 text-center">{lst.get('property_type','')}</td>
          <td class="py-2.5 px-3 text-center">
            <span class="px-2 py-0.5 rounded-full text-xs font-medium text-white" style="background:{clr}">{lst.get('source','')}</span>
          </td>
          <td class="py-2.5 px-3 text-sm text-center">{contact_cell}</td>
        </tr>"""

    # ── Scraper status badges ─────────────────────────────────────────────────
    status_badges = ""
    for s in scraper_status:
        ok = s["status"] == "success"
        cls = "bg-green-50 text-green-700 border-green-200" if ok else "bg-amber-50 text-amber-700 border-amber-200"
        icon = "✓" if ok else "↻"
        status_badges += (
            f'<div class="flex items-center gap-2 px-3 py-2 rounded-xl border {cls} text-sm">'
            f'<span class="font-bold text-base">{icon}</span>'
            f'<div><p class="font-semibold">{s["source"]}</p>'
            f'<p class="text-xs opacity-70">{s["count"]} listings</p></div></div>'
        )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>Hyderabad Real Estate — {ts_display}</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
  <style>body{{font-family:system-ui,-apple-system,sans-serif}}</style>
</head>
<body class="bg-gray-50 min-h-screen">

  <!-- Header -->
  <div class="bg-gradient-to-r from-indigo-900 via-indigo-800 to-purple-900 text-white sticky top-0 z-10 shadow-xl">
    <div class="max-w-7xl mx-auto px-4 py-5 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
      <div>
        <h1 class="text-xl font-bold tracking-tight">🏘️ Hyderabad Real Estate Intelligence</h1>
        <p class="text-indigo-300 text-xs mt-0.5">AI-powered · Claude Code · MagicBricks · 99acres · Housing.com · NoBroker · Square Yards</p>
      </div>
      <div class="text-right">
        <p class="text-indigo-300 text-xs uppercase tracking-widest">Report Generated</p>
        <p class="text-white font-bold text-base">{ts_display}</p>
      </div>
    </div>
  </div>

  <div class="max-w-7xl mx-auto px-4 py-8 space-y-10">

    <!-- KPI Cards -->
    <div class="grid grid-cols-2 lg:grid-cols-4 gap-4">
      <div class="bg-white rounded-2xl shadow-sm border border-gray-100 p-5">
        <p class="text-xs text-gray-400 uppercase tracking-wide">City Avg</p>
        <p class="text-3xl font-extrabold text-indigo-700 mt-1">Rs {summary.get('avg_price_per_sqft',0):,.0f}</p>
        <p class="text-xs text-gray-400 mt-1">per sq ft</p>
      </div>
      <div class="bg-white rounded-2xl shadow-sm border border-gray-100 p-5">
        <p class="text-xs text-gray-400 uppercase tracking-wide">YoY Growth</p>
        <p class="text-3xl font-extrabold text-green-600 mt-1">+{summary.get('yoy_change_pct',0):.1f}%</p>
        <p class="text-xs text-gray-400 mt-1">year on year</p>
      </div>
      <div class="bg-white rounded-2xl shadow-sm border border-gray-100 p-5">
        <p class="text-xs text-gray-400 uppercase tracking-wide">Hottest Area</p>
        <p class="text-xl font-extrabold text-rose-600 mt-1 leading-tight">{summary.get('hottest_locality','—')}</p>
        <p class="text-xs text-gray-400 mt-1">highest growth</p>
      </div>
      <div class="bg-white rounded-2xl shadow-sm border border-gray-100 p-5">
        <p class="text-xs text-gray-400 uppercase tracking-wide">New Launches</p>
        <p class="text-3xl font-extrabold text-amber-600 mt-1">{len(new_launches)}</p>
        <p class="text-xs text-gray-400 mt-1">projects tracked</p>
      </div>
    </div>

    <!-- AI Market Insights -->
    <div class="bg-gradient-to-br from-indigo-50 to-purple-50 rounded-2xl border border-indigo-100 p-6">
      <div class="flex items-center gap-3 mb-5">
        <div class="bg-indigo-600 rounded-xl p-2 text-white text-xl">✦</div>
        <div>
          <h2 class="text-lg font-bold text-gray-900">AI Market Analysis</h2>
          <p class="text-xs text-gray-500">Claude Code · {ts_display}</p>
        </div>
      </div>
      {insight_html}
    </div>

    <!-- Charts -->
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <div class="lg:col-span-2 bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
        <h2 class="text-base font-bold text-gray-900 mb-4">Price by Locality</h2>
        <canvas id="barChart" height="180"></canvas>
      </div>
      <div class="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
        <h2 class="text-base font-bold text-gray-900 mb-4">Property Mix</h2>
        <canvas id="pieChart" height="180"></canvas>
      </div>
    </div>

    <!-- New Launches -->
    <div>
      <div class="flex items-center gap-3 mb-5">
        <div class="bg-green-600 rounded-xl p-2 text-white text-xl">🚀</div>
        <div>
          <h2 class="text-lg font-bold text-gray-900">New Launches &amp; Upcoming Projects</h2>
          <p class="text-xs text-gray-500">MyHome · Aparna · Ramky · Prestige · Sobha · Brigade · Godrej &amp; more — June 2026</p>
          <p class="text-xs text-amber-600 mt-1">⚠️ Illustrative market intelligence — verify details directly with builders before investing.</p>
        </div>
      </div>
      <div class="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-5">
        {launch_cards}
      </div>
    </div>

    <!-- Locality Price Table -->
    <div class="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
      <div class="px-6 py-4 border-b border-gray-100">
        <h2 class="text-base font-bold text-gray-900">Locality-wise Prices</h2>
        <p class="text-xs text-gray-400 mt-0.5">All {len(localities)} micro-markets · June 2026</p>
      </div>
      <div class="overflow-x-auto">
        <table class="min-w-full text-sm">
          <thead class="bg-gray-50 text-xs font-semibold text-gray-500 uppercase tracking-wide">
            <tr>
              <th class="py-3 px-4 text-left">Locality</th>
              <th class="py-3 px-4 text-right">Avg Rs/sqft</th>
              <th class="py-3 px-4 text-right">Range</th>
              <th class="py-3 px-4 text-right">YoY</th>
              <th class="py-3 px-4 text-center">2BHK</th>
              <th class="py-3 px-4 text-center">3BHK</th>
              <th class="py-3 px-4 text-center">Demand</th>
              <th class="py-3 px-4 text-right">Listings</th>
            </tr>
          </thead>
          <tbody>{locality_rows}</tbody>
        </table>
      </div>
    </div>

    <!-- Listings Table -->
    <div class="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
      <div class="px-6 py-4 border-b border-gray-100">
        <h2 class="text-base font-bold text-gray-900">Recent Property Listings</h2>
        <p class="text-xs text-gray-400 mt-0.5">Top {min(40, len(listings))} of {len(listings)} listings · includes contact numbers &amp; posted dates</p>
      </div>
      <div class="overflow-x-auto">
        <table class="min-w-full text-sm">
          <thead class="bg-gray-50 text-xs font-semibold text-gray-500 uppercase tracking-wide">
            <tr>
              <th class="py-3 px-3 text-left">Posted</th>
              <th class="py-3 px-3 text-left">Property</th>
              <th class="py-3 px-3 text-left">Locality</th>
              <th class="py-3 px-3 text-right">Price</th>
              <th class="py-3 px-3 text-right">Area</th>
              <th class="py-3 px-3 text-right">Rs/sqft</th>
              <th class="py-3 px-3 text-center">BHK</th>
              <th class="py-3 px-3 text-center">Type</th>
              <th class="py-3 px-3 text-center">Source</th>
              <th class="py-3 px-3 text-center">Contact</th>
            </tr>
          </thead>
          <tbody>{listing_rows}</tbody>
        </table>
      </div>
    </div>

    <!-- Data Sources -->
    <div class="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
      <h2 class="text-base font-bold text-gray-900 mb-4">Data Sources Status</h2>
      <div class="flex flex-wrap gap-3">{status_badges}</div>
    </div>

    <p class="text-center text-xs text-gray-400 pb-4">
      Hyderabad Real Estate Intelligence · Claude Code · {ts_display}
    </p>
  </div>

  <script>
    new Chart(document.getElementById('barChart'), {{
      type:'bar',
      data:{{
        labels:{chart_labels},
        datasets:[
          {{label:'Avg Rs/sqft',data:{chart_prices},backgroundColor:'rgba(99,102,241,0.8)',borderRadius:5,yAxisID:'y'}},
          {{label:'YoY %',data:{chart_yoy},backgroundColor:'rgba(16,185,129,0.7)',borderRadius:5,yAxisID:'y2'}}
        ]
      }},
      options:{{responsive:true,plugins:{{legend:{{position:'top'}}}},
        scales:{{
          y:{{ticks:{{callback:v=>'Rs'+v.toLocaleString('en-IN')}}}},
          y2:{{position:'right',ticks:{{callback:v=>v+'%'}},grid:{{drawOnChartArea:false}}}},
          x:{{ticks:{{maxRotation:40,font:{{size:10}}}}}}
        }}
      }}
    }});
    new Chart(document.getElementById('pieChart'), {{
      type:'doughnut',
      data:{{labels:{pie_labels},datasets:[{{data:{pie_values},backgroundColor:['#6366f1','#10b981','#f59e0b','#ef4444','#8b5cf6']}}]}},
      options:{{responsive:true,plugins:{{legend:{{position:'bottom',labels:{{font:{{size:11}}}}}}}}}}
    }});
  </script>
</body>
</html>"""


# ── Email sender ─────────────────────────────────────────────────────────────

def send_email(html_path: Path, to_email: str, ts: datetime):
    smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USER", "")
    smtp_pass = os.getenv("SMTP_PASSWORD", "")
    from_email = os.getenv("REPORT_FROM", smtp_user)

    if not smtp_user or not smtp_pass:
        print("\n  [!] Email skipped — set SMTP_USER and SMTP_PASSWORD in backend/.env")
        print("      Gmail: use an App Password from https://myaccount.google.com/apppasswords")
        return False

    subject = f"Hyderabad Real Estate Report — {ts.strftime('%d %b %Y, %I:%M %p')}"

    msg = MIMEMultipart("mixed")
    msg["Subject"] = subject
    msg["From"]    = f"RE Intelligence <{from_email}>"
    msg["To"]      = to_email

    # Inline HTML body (mobile-friendly summary)
    html_content = html_path.read_text(encoding="utf-8")
    msg.attach(MIMEText(html_content, "html", "utf-8"))

    # Attachment
    part = MIMEBase("application", "octet-stream")
    part.set_payload(html_path.read_bytes())
    encoders.encode_base64(part)
    part.add_header("Content-Disposition", f'attachment; filename="{html_path.name}"')
    msg.attach(part)

    try:
        print(f"\n  Sending email to {to_email} via {smtp_host}:{smtp_port}...")
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.ehlo()
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.sendmail(from_email, to_email, msg.as_string())
        print(f"  Email sent!")
        return True
    except Exception as e:
        print(f"  [!] Email failed: {e}")
        return False


# ── Main ──────────────────────────────────────────────────────────────────────

async def main(email_to: str | None = None):
    ts = datetime.now()
    ts_file = ts.strftime("%Y-%m-%d_%H-%M")

    print(f"\n{'='*60}")
    print(f"  Hyderabad Real Estate Report Generator")
    print(f"  {ts.strftime('%d %B %Y, %I:%M %p')}")
    print(f"{'='*60}\n")

    agent_data, listings, scraper_status = await collect_data()

    print("  Building HTML report...")
    html = build_html(agent_data, listings, scraper_status, ts)

    out_dir  = Path(__file__).parent / "reports"
    out_dir.mkdir(exist_ok=True)
    out_file = out_dir / f"hyderabad_realestate_{ts_file}.html"
    out_file.write_text(html, encoding="utf-8")
    (out_dir / "latest.html").write_text(html, encoding="utf-8")

    launches  = agent_data.get("new_launches", [])
    summary   = agent_data.get("market_summary", {})
    size_kb   = out_file.stat().st_size / 1024

    print(f"\n{'='*60}")
    print(f"  Report ready!")
    print(f"  File      : {out_file}")
    print(f"  Size      : {size_kb:.1f} KB")
    print(f"  Localities: {len(agent_data.get('localities', []))}")
    print(f"  Listings  : {len(listings)}")
    print(f"  Launches  : {len(launches)}")
    print(f"  City avg  : Rs{summary.get('avg_price_per_sqft',0):,.0f}/sqft")
    print(f"  YoY       : +{summary.get('yoy_change_pct',0):.1f}%")
    print(f"  Hottest   : {summary.get('hottest_locality','')}")
    print(f"\n  Open: file://{out_file.resolve()}")
    print(f"{'='*60}\n")

    if email_to:
        send_email(out_file, email_to, ts)

    return str(out_file)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate Hyderabad Real Estate Report")
    parser.add_argument("--email", metavar="ADDRESS", help="Email the report to this address")
    args = parser.parse_args()
    asyncio.run(main(email_to=args.email))
