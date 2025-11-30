#!/usr/bin/env python3
"""MCP Server for Open-Meteo Weather API - Free Weather Data.

Provides tools for fetching weather forecasts, historical weather, and climate data.
Uses the free Open-Meteo API (no API key required).

Usage:
    python weather_server.py

Or via stdio transport:
    uv run python _mcp_servers/weather_server.py
"""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Any

import httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create MCP server
server = Server("weather")

# Open-Meteo API base URLs
GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
HISTORICAL_URL = "https://archive-api.open-meteo.com/v1/archive"

# HTTP client
http_client: httpx.AsyncClient | None = None


async def get_http_client() -> httpx.AsyncClient:
    """Get or create HTTP client."""
    global http_client
    if http_client is None:
        http_client = httpx.AsyncClient(timeout=30.0)
    return http_client


async def geocode_location(location: str) -> dict[str, Any] | None:
    """Convert location name to coordinates."""
    client = await get_http_client()
    response = await client.get(
        GEOCODING_URL,
        params={"name": location, "count": 1, "format": "json"},
    )
    response.raise_for_status()
    data = response.json()

    if not data.get("results"):
        return None

    result = data["results"][0]
    return {
        "name": result.get("name"),
        "country": result.get("country"),
        "admin1": result.get("admin1"),  # State/region
        "latitude": result.get("latitude"),
        "longitude": result.get("longitude"),
        "timezone": result.get("timezone"),
    }


@server.list_tools()
async def list_tools() -> list[Tool]:
    """List available weather tools."""
    return [
        Tool(
            name="get_current_weather",
            description="Get current weather conditions for a location. Returns temperature, humidity, wind, and conditions.",
            inputSchema={
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "City name or location (e.g., 'Seattle', 'New York', 'London, UK')",
                    },
                },
                "required": ["location"],
            },
        ),
        Tool(
            name="get_weather_forecast",
            description="Get weather forecast for the next 7 days. Includes daily high/low temperatures, precipitation probability, and conditions.",
            inputSchema={
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "City name or location",
                    },
                    "days": {
                        "type": "integer",
                        "description": "Number of forecast days (1-16)",
                        "default": 7,
                        "minimum": 1,
                        "maximum": 16,
                    },
                },
                "required": ["location"],
            },
        ),
        Tool(
            name="get_hourly_forecast",
            description="Get detailed hourly weather forecast for the next 48 hours. Useful for short-term planning.",
            inputSchema={
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "City name or location",
                    },
                },
                "required": ["location"],
            },
        ),
        Tool(
            name="get_historical_weather",
            description="Get historical weather data for a specific date range. Useful for analyzing seasonal patterns and trends.",
            inputSchema={
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "City name or location",
                    },
                    "start_date": {
                        "type": "string",
                        "description": "Start date in YYYY-MM-DD format",
                    },
                    "end_date": {
                        "type": "string",
                        "description": "End date in YYYY-MM-DD format",
                    },
                },
                "required": ["location", "start_date", "end_date"],
            },
        ),
        Tool(
            name="get_climate_averages",
            description="Get climate averages and typical weather patterns for a location. Based on historical data analysis.",
            inputSchema={
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "City name or location",
                    },
                },
                "required": ["location"],
            },
        ),
        Tool(
            name="get_weather_statistics",
            description="Get weather statistics for Monte Carlo simulations - temperature ranges, precipitation patterns, and seasonal variations.",
            inputSchema={
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "City name or location",
                    },
                    "metric": {
                        "type": "string",
                        "description": "Weather metric to analyze",
                        "enum": ["temperature", "precipitation", "sunshine", "wind"],
                        "default": "temperature",
                    },
                },
                "required": ["location"],
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    """Handle tool calls."""
    try:
        result = await _execute_tool(name, arguments)
        return [TextContent(type="text", text=json.dumps(result, indent=2, default=str))]
    except Exception as e:
        logger.exception(f"Error executing tool {name}")
        return [TextContent(type="text", text=json.dumps({"error": str(e)}))]


async def _execute_tool(name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    """Execute the specified tool with arguments."""
    if name == "get_current_weather":
        return await _get_current_weather(arguments["location"])
    elif name == "get_weather_forecast":
        return await _get_weather_forecast(
            arguments["location"],
            arguments.get("days", 7),
        )
    elif name == "get_hourly_forecast":
        return await _get_hourly_forecast(arguments["location"])
    elif name == "get_historical_weather":
        return await _get_historical_weather(
            arguments["location"],
            arguments["start_date"],
            arguments["end_date"],
        )
    elif name == "get_climate_averages":
        return await _get_climate_averages(arguments["location"])
    elif name == "get_weather_statistics":
        return await _get_weather_statistics(
            arguments["location"],
            arguments.get("metric", "temperature"),
        )
    else:
        return {"error": f"Unknown tool: {name}"}


def _interpret_weather_code(code: int) -> str:
    """Convert WMO weather code to description."""
    weather_codes = {
        0: "Clear sky",
        1: "Mainly clear",
        2: "Partly cloudy",
        3: "Overcast",
        45: "Fog",
        48: "Depositing rime fog",
        51: "Light drizzle",
        53: "Moderate drizzle",
        55: "Dense drizzle",
        56: "Light freezing drizzle",
        57: "Dense freezing drizzle",
        61: "Slight rain",
        63: "Moderate rain",
        65: "Heavy rain",
        66: "Light freezing rain",
        67: "Heavy freezing rain",
        71: "Slight snow",
        73: "Moderate snow",
        75: "Heavy snow",
        77: "Snow grains",
        80: "Slight rain showers",
        81: "Moderate rain showers",
        82: "Violent rain showers",
        85: "Slight snow showers",
        86: "Heavy snow showers",
        95: "Thunderstorm",
        96: "Thunderstorm with slight hail",
        99: "Thunderstorm with heavy hail",
    }
    return weather_codes.get(code, f"Unknown ({code})")


async def _get_current_weather(location: str) -> dict[str, Any]:
    """Get current weather conditions."""
    geo = await geocode_location(location)
    if not geo:
        return {"error": f"Location not found: {location}"}

    client = await get_http_client()
    response = await client.get(
        FORECAST_URL,
        params={
            "latitude": geo["latitude"],
            "longitude": geo["longitude"],
            "current": "temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,weather_code,wind_speed_10m,wind_direction_10m,cloud_cover",
            "timezone": geo.get("timezone", "auto"),
        },
    )
    response.raise_for_status()
    data = response.json()
    current = data.get("current", {})

    return {
        "location": {
            "name": geo["name"],
            "country": geo["country"],
            "region": geo.get("admin1"),
            "latitude": geo["latitude"],
            "longitude": geo["longitude"],
        },
        "current": {
            "temperature_c": current.get("temperature_2m"),
            "temperature_f": current.get("temperature_2m") * 9 / 5 + 32
            if current.get("temperature_2m")
            else None,
            "feels_like_c": current.get("apparent_temperature"),
            "humidity_pct": current.get("relative_humidity_2m"),
            "precipitation_mm": current.get("precipitation"),
            "weather_code": current.get("weather_code"),
            "weather_description": _interpret_weather_code(current.get("weather_code", 0)),
            "wind_speed_kmh": current.get("wind_speed_10m"),
            "wind_direction_deg": current.get("wind_direction_10m"),
            "cloud_cover_pct": current.get("cloud_cover"),
        },
        "timestamp": datetime.now().isoformat(),
    }


async def _get_weather_forecast(location: str, days: int = 7) -> dict[str, Any]:
    """Get daily weather forecast."""
    geo = await geocode_location(location)
    if not geo:
        return {"error": f"Location not found: {location}"}

    client = await get_http_client()
    response = await client.get(
        FORECAST_URL,
        params={
            "latitude": geo["latitude"],
            "longitude": geo["longitude"],
            "daily": "temperature_2m_max,temperature_2m_min,apparent_temperature_max,apparent_temperature_min,precipitation_sum,precipitation_probability_max,weather_code,sunrise,sunset,wind_speed_10m_max",
            "forecast_days": min(days, 16),
            "timezone": geo.get("timezone", "auto"),
        },
    )
    response.raise_for_status()
    data = response.json()
    daily = data.get("daily", {})

    forecast = []
    dates = daily.get("time", [])
    for i, date in enumerate(dates):
        forecast.append(
            {
                "date": date,
                "temperature_max_c": daily.get("temperature_2m_max", [None])[i],
                "temperature_min_c": daily.get("temperature_2m_min", [None])[i],
                "feels_like_max_c": daily.get("apparent_temperature_max", [None])[i],
                "feels_like_min_c": daily.get("apparent_temperature_min", [None])[i],
                "precipitation_mm": daily.get("precipitation_sum", [None])[i],
                "precipitation_probability_pct": daily.get(
                    "precipitation_probability_max", [None]
                )[i],
                "weather_code": daily.get("weather_code", [None])[i],
                "weather_description": _interpret_weather_code(
                    daily.get("weather_code", [0])[i] or 0
                ),
                "wind_speed_max_kmh": daily.get("wind_speed_10m_max", [None])[i],
                "sunrise": daily.get("sunrise", [None])[i],
                "sunset": daily.get("sunset", [None])[i],
            }
        )

    return {
        "location": {
            "name": geo["name"],
            "country": geo["country"],
            "region": geo.get("admin1"),
        },
        "forecast_days": len(forecast),
        "forecast": forecast,
    }


async def _get_hourly_forecast(location: str) -> dict[str, Any]:
    """Get hourly weather forecast."""
    geo = await geocode_location(location)
    if not geo:
        return {"error": f"Location not found: {location}"}

    client = await get_http_client()
    response = await client.get(
        FORECAST_URL,
        params={
            "latitude": geo["latitude"],
            "longitude": geo["longitude"],
            "hourly": "temperature_2m,relative_humidity_2m,precipitation_probability,precipitation,weather_code,wind_speed_10m",
            "forecast_hours": 48,
            "timezone": geo.get("timezone", "auto"),
        },
    )
    response.raise_for_status()
    data = response.json()
    hourly = data.get("hourly", {})

    forecast = []
    times = hourly.get("time", [])
    for i, time in enumerate(times[:48]):  # Limit to 48 hours
        forecast.append(
            {
                "time": time,
                "temperature_c": hourly.get("temperature_2m", [None])[i],
                "humidity_pct": hourly.get("relative_humidity_2m", [None])[i],
                "precipitation_probability_pct": hourly.get("precipitation_probability", [None])[
                    i
                ],
                "precipitation_mm": hourly.get("precipitation", [None])[i],
                "weather_code": hourly.get("weather_code", [None])[i],
                "weather_description": _interpret_weather_code(
                    hourly.get("weather_code", [0])[i] or 0
                ),
                "wind_speed_kmh": hourly.get("wind_speed_10m", [None])[i],
            }
        )

    return {
        "location": {
            "name": geo["name"],
            "country": geo["country"],
        },
        "hours": len(forecast),
        "hourly_forecast": forecast,
    }


async def _get_historical_weather(
    location: str,
    start_date: str,
    end_date: str,
) -> dict[str, Any]:
    """Get historical weather data."""
    geo = await geocode_location(location)
    if not geo:
        return {"error": f"Location not found: {location}"}

    client = await get_http_client()
    response = await client.get(
        HISTORICAL_URL,
        params={
            "latitude": geo["latitude"],
            "longitude": geo["longitude"],
            "start_date": start_date,
            "end_date": end_date,
            "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,rain_sum,snowfall_sum,wind_speed_10m_max",
            "timezone": geo.get("timezone", "auto"),
        },
    )
    response.raise_for_status()
    data = response.json()
    daily = data.get("daily", {})

    history = []
    dates = daily.get("time", [])
    for i, date in enumerate(dates):
        history.append(
            {
                "date": date,
                "temperature_max_c": daily.get("temperature_2m_max", [None])[i],
                "temperature_min_c": daily.get("temperature_2m_min", [None])[i],
                "precipitation_mm": daily.get("precipitation_sum", [None])[i],
                "rain_mm": daily.get("rain_sum", [None])[i],
                "snowfall_cm": daily.get("snowfall_sum", [None])[i],
                "wind_speed_max_kmh": daily.get("wind_speed_10m_max", [None])[i],
            }
        )

    # Calculate summary statistics
    temps_max = [h["temperature_max_c"] for h in history if h["temperature_max_c"] is not None]
    temps_min = [h["temperature_min_c"] for h in history if h["temperature_min_c"] is not None]
    precip = [h["precipitation_mm"] for h in history if h["precipitation_mm"] is not None]

    return {
        "location": {
            "name": geo["name"],
            "country": geo["country"],
        },
        "period": {
            "start": start_date,
            "end": end_date,
            "days": len(history),
        },
        "summary": {
            "avg_high_c": sum(temps_max) / len(temps_max) if temps_max else None,
            "avg_low_c": sum(temps_min) / len(temps_min) if temps_min else None,
            "max_temp_c": max(temps_max) if temps_max else None,
            "min_temp_c": min(temps_min) if temps_min else None,
            "total_precipitation_mm": sum(precip) if precip else None,
            "rainy_days": sum(1 for p in precip if p and p > 0),
        },
        "history": history[-30:],  # Limit to last 30 days
    }


async def _get_climate_averages(location: str) -> dict[str, Any]:
    """Get climate averages based on historical data."""
    geo = await geocode_location(location)
    if not geo:
        return {"error": f"Location not found: {location}"}

    # Get last year's data as a proxy for climate
    end_date = datetime.now() - timedelta(days=30)
    start_date = end_date - timedelta(days=365)

    client = await get_http_client()
    response = await client.get(
        HISTORICAL_URL,
        params={
            "latitude": geo["latitude"],
            "longitude": geo["longitude"],
            "start_date": start_date.strftime("%Y-%m-%d"),
            "end_date": end_date.strftime("%Y-%m-%d"),
            "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,sunshine_duration",
            "timezone": geo.get("timezone", "auto"),
        },
    )
    response.raise_for_status()
    data = response.json()
    daily = data.get("daily", {})

    # Group by month
    monthly_stats = {}
    dates = daily.get("time", [])
    for i, date in enumerate(dates):
        month = date[:7]  # YYYY-MM
        if month not in monthly_stats:
            monthly_stats[month] = {"temps_max": [], "temps_min": [], "precip": []}

        if daily.get("temperature_2m_max", [None])[i] is not None:
            monthly_stats[month]["temps_max"].append(daily["temperature_2m_max"][i])
        if daily.get("temperature_2m_min", [None])[i] is not None:
            monthly_stats[month]["temps_min"].append(daily["temperature_2m_min"][i])
        if daily.get("precipitation_sum", [None])[i] is not None:
            monthly_stats[month]["precip"].append(daily["precipitation_sum"][i])

    # Calculate monthly averages
    monthly_averages = []
    for month, stats in sorted(monthly_stats.items()):
        month_name = datetime.strptime(month, "%Y-%m").strftime("%B")
        monthly_averages.append(
            {
                "month": month_name,
                "avg_high_c": sum(stats["temps_max"]) / len(stats["temps_max"])
                if stats["temps_max"]
                else None,
                "avg_low_c": sum(stats["temps_min"]) / len(stats["temps_min"])
                if stats["temps_min"]
                else None,
                "avg_precipitation_mm": sum(stats["precip"]) / len(stats["precip"])
                if stats["precip"]
                else None,
                "total_precipitation_mm": sum(stats["precip"]) if stats["precip"] else None,
            }
        )

    return {
        "location": {
            "name": geo["name"],
            "country": geo["country"],
            "region": geo.get("admin1"),
        },
        "data_period": f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}",
        "monthly_averages": monthly_averages,
    }


async def _get_weather_statistics(location: str, metric: str = "temperature") -> dict[str, Any]:
    """Get weather statistics for Monte Carlo simulations."""
    geo = await geocode_location(location)
    if not geo:
        return {"error": f"Location not found: {location}"}

    # Get 2 years of historical data
    end_date = datetime.now() - timedelta(days=30)
    start_date = end_date - timedelta(days=730)

    params: dict[str, Any] = {
        "latitude": geo["latitude"],
        "longitude": geo["longitude"],
        "start_date": start_date.strftime("%Y-%m-%d"),
        "end_date": end_date.strftime("%Y-%m-%d"),
        "timezone": geo.get("timezone", "auto"),
    }

    metric_fields = {
        "temperature": "temperature_2m_max,temperature_2m_min",
        "precipitation": "precipitation_sum,rain_sum,snowfall_sum",
        "sunshine": "sunshine_duration",
        "wind": "wind_speed_10m_max,wind_gusts_10m_max",
    }
    params["daily"] = metric_fields.get(metric, metric_fields["temperature"])

    client = await get_http_client()
    response = await client.get(HISTORICAL_URL, params=params)
    response.raise_for_status()
    data = response.json()
    daily = data.get("daily", {})

    # Calculate statistics based on metric
    import statistics

    stats: dict[str, Any] = {
        "location": {
            "name": geo["name"],
            "country": geo["country"],
        },
        "metric": metric,
        "data_period": f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}",
        "data_points": len(daily.get("time", [])),
    }

    if metric == "temperature":
        temps_max = [t for t in daily.get("temperature_2m_max", []) if t is not None]
        temps_min = [t for t in daily.get("temperature_2m_min", []) if t is not None]

        if temps_max:
            stats["high_temperature"] = {
                "mean": statistics.mean(temps_max),
                "std_dev": statistics.stdev(temps_max) if len(temps_max) > 1 else 0,
                "min": min(temps_max),
                "max": max(temps_max),
                "percentile_5": sorted(temps_max)[int(len(temps_max) * 0.05)],
                "percentile_95": sorted(temps_max)[int(len(temps_max) * 0.95)],
            }
        if temps_min:
            stats["low_temperature"] = {
                "mean": statistics.mean(temps_min),
                "std_dev": statistics.stdev(temps_min) if len(temps_min) > 1 else 0,
                "min": min(temps_min),
                "max": max(temps_min),
                "percentile_5": sorted(temps_min)[int(len(temps_min) * 0.05)],
                "percentile_95": sorted(temps_min)[int(len(temps_min) * 0.95)],
            }

    elif metric == "precipitation":
        precip = [p for p in daily.get("precipitation_sum", []) if p is not None]
        if precip:
            stats["precipitation"] = {
                "mean_daily_mm": statistics.mean(precip),
                "std_dev": statistics.stdev(precip) if len(precip) > 1 else 0,
                "max_daily_mm": max(precip),
                "days_with_rain": sum(1 for p in precip if p > 0),
                "days_with_rain_pct": sum(1 for p in precip if p > 0) / len(precip) * 100,
                "percentile_90": sorted(precip)[int(len(precip) * 0.90)],
            }

    elif metric == "wind":
        wind = [w for w in daily.get("wind_speed_10m_max", []) if w is not None]
        if wind:
            stats["wind_speed"] = {
                "mean_kmh": statistics.mean(wind),
                "std_dev": statistics.stdev(wind) if len(wind) > 1 else 0,
                "max_kmh": max(wind),
                "percentile_95": sorted(wind)[int(len(wind) * 0.95)],
            }

    return stats


async def main():
    """Run the MCP server."""
    logger.info("Starting weather MCP server (Open-Meteo)...")
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
