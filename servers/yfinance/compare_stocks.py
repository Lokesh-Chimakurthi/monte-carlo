"""Auto-generated wrapper for yfinance → compare_stocks."""

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

TOOL = {'description': 'Compare key metrics across multiple stocks for competitive analysis.', 'inputSchema': {'properties': {'symbols': {'description': 'List of stock ticker symbols to compare (max 5)', 'items': {'type': 'string'}, 'type': 'array'}}, 'required': ['symbols'], 'type': 'object'}, 'name': 'compare_stocks'}

async def compare_stocks(*args: Any, **kwargs: Any) -> Any:
    """Compare key metrics across multiple stocks for competitive analysis."""
    return await call_tool("yfinance", TOOL, *args, **kwargs)

__all__ = ('TOOL', 'compare_stocks')
