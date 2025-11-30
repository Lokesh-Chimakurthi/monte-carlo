"""Auto-generated wrapper for weather → get_current_weather."""

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

TOOL = {'description': 'Get current weather conditions for a location. Returns temperature, humidity, wind, and conditions.', 'inputSchema': {'properties': {'location': {'description': "City name or location (e.g., 'Seattle', 'New York', 'London, UK')", 'type': 'string'}}, 'required': ['location'], 'type': 'object'}, 'name': 'get_current_weather'}

async def get_current_weather(*args: Any, **kwargs: Any) -> Any:
    """Get current weather conditions for a location. Returns temperature, humidity, wind, and conditions."""
    return await call_tool("weather", TOOL, *args, **kwargs)

__all__ = ('TOOL', 'get_current_weather')
