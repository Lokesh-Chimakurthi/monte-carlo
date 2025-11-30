"""Auto-generated wrapper for weather → get_weather_forecast."""

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

TOOL = {'description': 'Get weather forecast for the next 7 days. Includes daily high/low temperatures, precipitation probability, and conditions.', 'inputSchema': {'properties': {'days': {'default': 7, 'description': 'Number of forecast days (1-16)', 'maximum': 16, 'minimum': 1, 'type': 'integer'}, 'location': {'description': 'City name or location', 'type': 'string'}}, 'required': ['location'], 'type': 'object'}, 'name': 'get_weather_forecast'}

async def get_weather_forecast(*args: Any, **kwargs: Any) -> Any:
    """Get weather forecast for the next 7 days. Includes daily high/low temperatures, precipitation probability, and conditions."""
    return await call_tool("weather", TOOL, *args, **kwargs)

__all__ = ('TOOL', 'get_weather_forecast')
