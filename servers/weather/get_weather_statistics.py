"""Auto-generated wrapper for weather → get_weather_statistics."""

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

TOOL = {'description': 'Get weather statistics for Monte Carlo simulations - temperature ranges, precipitation patterns, and seasonal variations.', 'inputSchema': {'properties': {'location': {'description': 'City name or location', 'type': 'string'}, 'metric': {'default': 'temperature', 'description': 'Weather metric to analyze', 'enum': ['temperature', 'precipitation', 'sunshine', 'wind'], 'type': 'string'}}, 'required': ['location'], 'type': 'object'}, 'name': 'get_weather_statistics'}

async def get_weather_statistics(*args: Any, **kwargs: Any) -> Any:
    """Get weather statistics for Monte Carlo simulations - temperature ranges, precipitation patterns, and seasonal variations."""
    return await call_tool("weather", TOOL, *args, **kwargs)

__all__ = ('TOOL', 'get_weather_statistics')
