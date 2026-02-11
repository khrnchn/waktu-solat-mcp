"""MCP server exposing Malaysian prayer times via Waktu Solat API."""

import base64
import json
import os
from datetime import datetime, timedelta, timezone
from contextlib import asynccontextmanager

from starlette.requests import Request
from starlette.responses import HTMLResponse
from starlette.routing import Route

from mcp.server.fastmcp import FastMCP

from .api import WaktuSolatAPI, WaktuSolatAPIError


MYT = timezone(timedelta(hours=8))

PRAYER_NAMES = [
    ("fajr", "Subuh/Fajr"),
    ("syuruk", "Syuruk/Sunrise"),
    ("dhuhr", "Zohor/Dhuhr"),
    ("asr", "Asar/Asr"),
    ("maghrib", "Maghrib"),
    ("isha", "Isyak/Isha"),
]


def _timestamp_to_myt_str(ts: int) -> str:
    """Convert Unix timestamp to human-readable time in MYT."""
    dt = datetime.fromtimestamp(ts, tz=MYT)
    return dt.strftime("%I:%M %p")  # "05:42 AM" style


mcp = FastMCP("waktusolat")


@asynccontextmanager
async def get_api():
    api = WaktuSolatAPI()
    try:
        yield api
    finally:
        await api.close()


@mcp.tool()
async def get_prayer_times_today(zone: str) -> str:
    """
    Get prayer times for today in the given zone.
    Zone codes follow JAKIM format (e.g. SGR01, WLY01).
    Returns times in Malaysia time (MYT, UTC+8).
    """
    zone = zone.strip().upper()
    async with get_api() as api:
        try:
            data = await api.get_prayer_times(zone)
        except WaktuSolatAPIError as e:
            return f"Error: {e}"
    zone_name = data.get("zone", zone)
    year = data.get("year")
    month = data.get("month", "")
    prayers_list = data.get("prayers", [])
    now_myt = datetime.now(tz=MYT)
    today = now_myt.day
    today_entry = next((p for p in prayers_list if p["day"] == today), None)
    if not today_entry:
        return (
            f"No prayer data for today (zone {zone_name}). "
            f"Month has days 1-{max(p.get('day', 0) for p in prayers_list) or 28}."
        )
    lines = [
        f"Prayer times for zone {zone_name}",
        f"Date: {now_myt.strftime('%d %B %Y')} ({today_entry.get('hijri', '')})",
        "",
    ]
    for key, label in PRAYER_NAMES:
        ts = today_entry.get(key)
        if ts is not None:
            lines.append(f"  {label}: {_timestamp_to_myt_str(ts)}")
    return "\n".join(lines)


@mcp.tool()
async def get_prayer_times_month(zone: str, year: int, month: int) -> str:
    """
    Get prayer times for all days in a given month.
    Zone codes follow JAKIM format (e.g. SGR01).
    """
    zone = zone.strip().upper()
    async with get_api() as api:
        try:
            data = await api.get_prayer_times(zone, year, month)
        except WaktuSolatAPIError as e:
            return f"Error: {e}"
    zone_name = data.get("zone", zone)
    month_name = data.get("month", str(month))
    prayers_list = data.get("prayers", [])
    lines = [
        f"Prayer times for zone {zone_name}, {month_name} {year}",
        "",
        "Day | Hijri     | Subuh   | Syuruk  | Zohor   | Asar    | Maghrib | Isyak",
        "-" * 75,
    ]
    for p in prayers_list:
        day = p.get("day", 0)
        hijri = p.get("hijri", "")
        fajr = _timestamp_to_myt_str(p["fajr"]) if p.get("fajr") else "-"
        syuruk = _timestamp_to_myt_str(p["syuruk"]) if p.get("syuruk") else "-"
        dhuhr = _timestamp_to_myt_str(p["dhuhr"]) if p.get("dhuhr") else "-"
        asr = _timestamp_to_myt_str(p["asr"]) if p.get("asr") else "-"
        maghrib = _timestamp_to_myt_str(p["maghrib"]) if p.get("maghrib") else "-"
        isha = _timestamp_to_myt_str(p["isha"]) if p.get("isha") else "-"
        lines.append(f"{day:3} | {hijri:9} | {fajr:7} | {syuruk:7} | {dhuhr:7} | {asr:7} | {maghrib:7} | {isha}")
    return "\n".join(lines)


@mcp.tool()
async def get_next_prayer(zone: str) -> str:
    """
    Get the next upcoming prayer time for the given zone.
    If all prayers today have passed, returns next day's Fajr/Subuh.
    """
    zone = zone.strip().upper()
    async with get_api() as api:
        try:
            data = await api.get_prayer_times(zone)
        except WaktuSolatAPIError as e:
            return f"Error: {e}"
    prayers_list = data.get("prayers", [])
    now_myt = datetime.now(tz=MYT)
    today = now_myt.day
    now_ts = now_myt.timestamp()
    today_entry = next((p for p in prayers_list if p["day"] == today), None)
    if not today_entry:
        return f"No prayer data for today in zone {zone}."
    prayer_order = [("fajr", "Subuh/Fajr"), ("syuruk", "Syuruk"), ("dhuhr", "Zohor/Dhuhr"), ("asr", "Asar/Asr"), ("maghrib", "Maghrib"), ("isha", "Isyak/Isha")]
    for key, label in prayer_order:
        ts = today_entry.get(key)
        if ts is not None and ts > now_ts:
            remaining = int(ts - now_ts)
            mins, secs = divmod(remaining, 60)
            hrs, mins = divmod(mins, 60)
            if hrs > 0:
                remaining_str = f"{hrs}h {mins}m"
            else:
                remaining_str = f"{mins}m"
            return f"Next prayer: {label} at {_timestamp_to_myt_str(ts)} (in {remaining_str})"
    tomorrow_entry = next((p for p in prayers_list if p["day"] == today + 1), None)
    if tomorrow_entry and tomorrow_entry.get("fajr"):
        ts = tomorrow_entry["fajr"]
        remaining = int(ts - now_ts)
        mins, secs = divmod(remaining, 60)
        hrs, mins = divmod(mins, 60)
        if hrs > 0:
            remaining_str = f"{hrs}h {mins}m"
        else:
            remaining_str = f"{mins}m"
        return f"All prayers today have passed. Next: Subuh/Fajr (tomorrow) at {_timestamp_to_myt_str(ts)} (in {remaining_str})"
    return "All prayers for today have passed. No tomorrow data in current month."


@mcp.tool()
async def list_zones(state: str | None = None) -> str:
    """
    List JAKIM prayer zone codes with area descriptions.
    Optionally filter by state code (e.g. SGR, JHR, WLY).
    """
    async with get_api() as api:
        try:
            zones = await api.get_zones(state)
        except WaktuSolatAPIError as e:
            return f"Error: {e}"
    if not zones:
        return "No zones found."
    lines = ["Zone   | State              | Area", "-" * 60]
    for z in zones:
        code = z.get("jakimCode", "")
        negeri = z.get("negeri", "")
        daerah = z.get("daerah", "")
        lines.append(f"{code:6} | {negeri:18} | {daerah}")
    return "\n".join(lines)


def _landing_page_html(base_url: str) -> str:
    """Generate landing page HTML with Add to Cursor/Claude."""
    mcp_url = base_url.rstrip("/") + "/mcp"
    config = {"waktusolat": {"url": mcp_url}}
    config_b64 = base64.urlsafe_b64encode(json.dumps(config).encode()).decode()
    cursor_link = f"cursor://anysphere.cursor-deeplink/mcp/install?name=waktusolat&config={config_b64}"
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Waktu Solat MCP</title>
  <style>
    * {{ box-sizing: border-box; }}
    body {{ font-family: system-ui, sans-serif; max-width: 480px; margin: 2rem auto; padding: 0 1rem; line-height: 1.6; color: #333; }}
    h1 {{ font-size: 1.5rem; margin-bottom: 0.5rem; }}
    p {{ color: #666; margin: 0 0 1.5rem; }}
    .card {{ background: #f8f9fa; border-radius: 8px; padding: 1rem; margin-bottom: 1rem; }}
    .card h2 {{ font-size: 1rem; margin: 0 0 0.5rem; }}
    .card p {{ margin: 0 0 0.75rem; font-size: 0.9rem; }}
    a.btn {{ display: inline-block; background: #1a1a1a; color: white; padding: 0.5rem 1rem; border-radius: 6px; text-decoration: none; font-size: 0.9rem; }}
    a.btn:hover {{ background: #333; }}
    code {{ background: #eee; padding: 0.2em 0.4em; border-radius: 4px; font-size: 0.85em; word-break: break-all; }}
    .url {{ font-size: 0.8rem; margin-top: 0.5rem; }}
  </style>
</head>
<body>
  <h1>Waktu Solat MCP</h1>
  <p>Malaysian prayer times for Claude, Cursor, and other MCP clients.</p>

  <div class="card">
    <h2>Add to Cursor</h2>
    <p>One-click install.</p>
    <a href="{cursor_link}" class="btn">Add to Cursor</a>
  </div>

  <div class="card">
    <h2>Add to Claude</h2>
    <p>In Claude: Settings → Connectors → Add custom connector. Use this URL:</p>
    <code class="url">{mcp_url}</code>
  </div>

  <div class="card">
    <h2>Run locally</h2>
    <p><code>uv sync && uv run waktusolat-mcp</code></p>
    <a href="https://github.com/khrnchn/waktu-solat-mcp" class="btn">View on GitHub</a>
  </div>
</body>
</html>"""


async def _landing_page(request: Request) -> HTMLResponse:
    # Allow override for proxies (Railway, etc.) that may not set forwarded headers
    base_url = os.getenv("MCP_BASE_URL") or str(request.base_url).rstrip("/")
    return HTMLResponse(_landing_page_html(base_url))


def main() -> None:
    transport = os.getenv("MCP_TRANSPORT", "stdio")
    if transport == "streamable-http":
        mcp.settings.host = "0.0.0.0"
        mcp.settings.port = int(os.getenv("PORT", os.getenv("FASTMCP_PORT", "8000")))
        mcp._custom_starlette_routes.append(Route("/", _landing_page))
        mcp.run(transport="streamable-http")
    else:
        mcp.run(transport="stdio")


def main_http() -> None:
    """Convenience entry point for HTTP mode (hosting)."""
    os.environ["MCP_TRANSPORT"] = "streamable-http"
    main()
