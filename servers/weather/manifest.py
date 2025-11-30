"""Tool manifest for weather.

Provides lightweight search + schema lookup so sandboxes can discover tools without
loading every wrapper module.
"""

from __future__ import annotations

from typing import Any, List

TOOLS: List[dict[str, Any]] = [{'description': 'Get current weather conditions for a location. Returns temperature, humidity, wind, and conditions.', 'inputSchema': {'properties': {'location': {'description': "City name or location (e.g., 'Seattle', 'New York', 'London, UK')", 'type': 'string'}}, 'required': ['location'], 'type': 'object'}, 'name': 'get_current_weather'}, {'description': 'Get weather forecast for the next 7 days. Includes daily high/low temperatures, precipitation probability, and conditions.', 'inputSchema': {'properties': {'days': {'default': 7, 'description': 'Number of forecast days (1-16)', 'maximum': 16, 'minimum': 1, 'type': 'integer'}, 'location': {'description': 'City name or location', 'type': 'string'}}, 'required': ['location'], 'type': 'object'}, 'name': 'get_weather_forecast'}, {'description': 'Get detailed hourly weather forecast for the next 48 hours. Useful for short-term planning.', 'inputSchema': {'properties': {'location': {'description': 'City name or location', 'type': 'string'}}, 'required': ['location'], 'type': 'object'}, 'name': 'get_hourly_forecast'}, {'description': 'Get historical weather data for a specific date range. Useful for analyzing seasonal patterns and trends.', 'inputSchema': {'properties': {'end_date': {'description': 'End date in YYYY-MM-DD format', 'type': 'string'}, 'location': {'description': 'City name or location', 'type': 'string'}, 'start_date': {'description': 'Start date in YYYY-MM-DD format', 'type': 'string'}}, 'required': ['location', 'start_date', 'end_date'], 'type': 'object'}, 'name': 'get_historical_weather'}, {'description': 'Get climate averages and typical weather patterns for a location. Based on historical data analysis.', 'inputSchema': {'properties': {'location': {'description': 'City name or location', 'type': 'string'}}, 'required': ['location'], 'type': 'object'}, 'name': 'get_climate_averages'}, {'description': 'Get weather statistics for Monte Carlo simulations - temperature ranges, precipitation patterns, and seasonal variations.', 'inputSchema': {'properties': {'location': {'description': 'City name or location', 'type': 'string'}, 'metric': {'default': 'temperature', 'description': 'Weather metric to analyze', 'enum': ['temperature', 'precipitation', 'sunshine', 'wind'], 'type': 'string'}}, 'required': ['location'], 'type': 'object'}, 'name': 'get_weather_statistics'}]


def search_tools(query: str) -> List[dict[str, Any]]:
    """Return tools whose name or description contains the query (case-insensitive)."""

    normalized = (query or "").strip().lower()
    if not normalized:
        return list(TOOLS)
    results: list[dict[str, Any]] = []
    for tool in TOOLS:
        name = str(tool.get("name", "")).lower()
        description = str(tool.get("description", "")).lower()
        if normalized in name or normalized in description:
            results.append(tool)
    return results


__all__ = ("TOOLS", "search_tools")
