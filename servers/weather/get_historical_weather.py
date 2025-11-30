"""Auto-generated wrapper for weather → get_historical_weather."""

from __future__ import annotations

from pathlib import Path
from typing import Any

try:
    from servers._runtime import call_tool
except ImportError:  # Modal uploads omit the 'servers' package
    import sys
    root = Path(__file__).resolve().parent.parent
    root_str = str(root)
    if root_str not in sys.path:
        sys.path.append(root_str)
    from _runtime import call_tool

TOOL = {'description': 'Get historical weather data for a specific date range. Useful for analyzing seasonal patterns and trends.', 'inputSchema': {'properties': {'end_date': {'description': 'End date in YYYY-MM-DD format', 'type': 'string'}, 'location': {'description': 'City name or location', 'type': 'string'}, 'start_date': {'description': 'Start date in YYYY-MM-DD format', 'type': 'string'}}, 'required': ['location', 'start_date', 'end_date'], 'type': 'object'}, 'name': 'get_historical_weather'}

async def get_historical_weather(*args: Any, **kwargs: Any) -> Any:
    """Get historical weather data for a specific date range. Useful for analyzing seasonal patterns and trends."""
    return await call_tool("weather", TOOL, *args, **kwargs)

__all__ = ('TOOL', 'get_historical_weather')
