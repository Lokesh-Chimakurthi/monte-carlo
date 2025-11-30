"""Auto-generated wrapper for weather → get_climate_averages."""

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

TOOL = {'description': 'Get climate averages and typical weather patterns for a location. Based on historical data analysis.', 'inputSchema': {'properties': {'location': {'description': 'City name or location', 'type': 'string'}}, 'required': ['location'], 'type': 'object'}, 'name': 'get_climate_averages'}

async def get_climate_averages(*args: Any, **kwargs: Any) -> Any:
    """Get climate averages and typical weather patterns for a location. Based on historical data analysis."""
    return await call_tool("weather", TOOL, *args, **kwargs)

__all__ = ('TOOL', 'get_climate_averages')
