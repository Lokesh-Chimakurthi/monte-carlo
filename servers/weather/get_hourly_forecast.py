"""Auto-generated wrapper for weather → get_hourly_forecast."""

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

TOOL = {'description': 'Get detailed hourly weather forecast for the next 48 hours. Useful for short-term planning.', 'inputSchema': {'properties': {'location': {'description': 'City name or location', 'type': 'string'}}, 'required': ['location'], 'type': 'object'}, 'name': 'get_hourly_forecast'}

async def get_hourly_forecast(*args: Any, **kwargs: Any) -> Any:
    """Get detailed hourly weather forecast for the next 48 hours. Useful for short-term planning."""
    return await call_tool("weather", TOOL, *args, **kwargs)

__all__ = ('TOOL', 'get_hourly_forecast')
